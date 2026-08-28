"""Interfaz Streamlit para la corrección masiva de tareas universitarias mediante LLM."""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core.data import COURSES
from core.docx_generator import feedback_filename, generar_docx_feedback
from core.evaluator import EvaluationError, Evaluacion, evaluar_entrega
from core.parser import (
    SUPPORTED_EXTENSIONS,
    ExtractedDocument,
    FileExtractionError,
    UnsupportedFileTypeError,
    extract_text,
)
from core.theme import LOGO_PATH, inject_theme, render_header

load_dotenv()

RUBRICS_DIR = Path(__file__).parent / "rubrics"

GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-2.5-flash", "gemini-2.5-pro"]
ANTHROPIC_MODELS = ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"]
MODELO_PERSONALIZADO = "Otro (escribir manualmente)"

st.set_page_config(
    page_title="Corrector OpenBeauchef",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📝",
    layout="wide",
)


def _load_rubric_files() -> dict[str, str]:
    if not RUBRICS_DIR.exists():
        return {}
    files = {}
    for path in sorted(RUBRICS_DIR.glob("*")):
        if path.suffix.lower() in (".txt", ".md", ".json"):
            files[path.name] = path.read_text(encoding="utf-8")
    return files


def _sidebar_config() -> dict:
    st.sidebar.header("⚙️ Configuración del Modelo")

    provider_label = st.sidebar.radio(
        "Proveedor de LLM",
        options=["Google Gemini (gratuito)", "Anthropic Claude"],
        index=0,
    )
    provider = "gemini" if provider_label.startswith("Google") else "anthropic"

    env_key_name = "GEMINI_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
    default_key = os.getenv(env_key_name, "")

    api_key = st.sidebar.text_input(
        f"API Key ({env_key_name})",
        value=default_key,
        type="password",
        help="Se puede definir también en el archivo .env",
    )

    model_options = (GEMINI_MODELS if provider == "gemini" else ANTHROPIC_MODELS) + [MODELO_PERSONALIZADO]
    model_choice = st.sidebar.selectbox("Modelo", options=model_options, index=0)

    if model_choice == MODELO_PERSONALIZADO:
        model = st.sidebar.text_input(
            "Nombre exacto del modelo",
            help="Ej: gemini-3.6-flash. Útil si Google/Anthropic cambian nombres de modelos.",
        )
    else:
        model = model_choice

    st.sidebar.divider()
    st.sidebar.subheader("Escala de Notas")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        escala_min = st.number_input("Mínima", value=1.0, step=0.5)
    with col2:
        escala_max = st.number_input("Máxima", value=7.0, step=0.5)

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "escala_min": escala_min,
        "escala_max": escala_max,
    }


def _rubric_editor() -> str:
    with st.container(key="rubric_card"):
        st.subheader("📋 Rúbrica Activa")

        rubric_files = _load_rubric_files()
        options = ["(Rúbrica personalizada)"] + list(rubric_files.keys())
        selected = st.selectbox("Cargar rúbrica desde archivo", options=options)

        default_text = rubric_files.get(selected, "") if selected != "(Rúbrica personalizada)" else ""

        rubrica_texto = st.text_area(
            "Edita o pega aquí la rúbrica de la semana (criterios, puntajes máximos y descripciones):",
            value=default_text,
            height=280,
            key=f"rubrica_{selected}",
        )
    return rubrica_texto


def _extract_zip(uploaded_zip, dest_dir: Path) -> list[Path]:
    zip_path = dest_dir / "entregas.zip"
    with open(zip_path, "wb") as f:
        f.write(uploaded_zip.getbuffer())

    extract_dir = dest_dir / "extraidos"
    extract_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    valid_files = [
        p for p in extract_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith("~$")
    ]
    return sorted(valid_files)


def main() -> None:
    inject_theme()
    render_header(
        "Corrector Masivo de Tareas",
        "Define la rúbrica, elige tu flujo de trabajo y deja que el LLM genere el feedback en Word.",
    )

    config = _sidebar_config()
    rubrica_texto = _rubric_editor()

    st.divider()

    tab_curso, tab_lote = st.tabs(["🎓 Por curso y auxiliar", "📦 Por lote (ZIP)"])

    with tab_curso:
        _render_course_flow(rubrica_texto, config)

    with tab_lote:
        _render_batch_flow(rubrica_texto, config)


# ---------------------------------------------------------------------------
# Flujo 1: selección de curso / auxiliar / estudiante, corrección individual
# ---------------------------------------------------------------------------

def _correction_key(curso: str, auxiliar: str, estudiante: str) -> str:
    return f"{curso}::{auxiliar}::{estudiante}"


TIPO_ARCHIVO_LABEL = {
    ".pdf": "documento PDF",
    ".docx": "documento Word",
    ".csv": "planilla CSV",
    ".xlsx": "planilla Excel",
    ".xls": "planilla Excel",
}


def _extract_uploaded_file(uploaded_file) -> ExtractedDocument:
    """Guarda un UploadedFile en disco temporalmente y extrae su texto/datos."""
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)

    try:
        extraido = extract_text(tmp_path)
        return extraido
    finally:
        tmp_path.unlink(missing_ok=True)


def _combine_extracted_files(uploaded_files: list) -> tuple[str, str]:
    """Extrae y combina el contenido de varios archivos de una misma entrega.

    Devuelve (contenido_combinado, etiqueta_de_archivos) para pasar al evaluador
    y para dejar constancia en el .docx generado.
    """
    secciones: list[str] = []
    nombres: list[str] = []

    for uploaded_file in uploaded_files:
        try:
            extraido = _extract_uploaded_file(uploaded_file)
        except (UnsupportedFileTypeError, FileExtractionError) as exc:
            raise type(exc)(f"{uploaded_file.name}: {exc}") from exc

        suffix = Path(uploaded_file.name).suffix.lower()
        tipo = TIPO_ARCHIVO_LABEL.get(suffix, suffix)
        secciones.append(f"=== Archivo: {uploaded_file.name} ({tipo}) ===\n{extraido.text}")
        nombres.append(uploaded_file.name)

    contenido = "\n\n".join(secciones)
    etiqueta = ", ".join(nombres)
    return contenido, etiqueta


def _process_multi_submission(
    uploaded_files: list, estudiante: str, rubrica_texto: str, config: dict
) -> tuple[Evaluacion, bytes, str]:
    """Extrae texto de todos los archivos de la entrega, evalúa con el LLM y genera el .docx."""
    contenido, etiqueta_archivos = _combine_extracted_files(uploaded_files)

    evaluacion = evaluar_entrega(
        provider=config["provider"],
        api_key=config["api_key"],
        model=config["model"],
        rubrica=rubrica_texto,
        filename=etiqueta_archivos,
        contenido=contenido,
        escala_min=config["escala_min"],
        escala_max=config["escala_max"],
    )

    docx_buffer = generar_docx_feedback(evaluacion, etiqueta_archivos)
    nombre_archivo = estudiante.replace(",", "").replace(" ", "_")
    out_name = f"Feedback_{nombre_archivo}.docx"
    return evaluacion, docx_buffer.getvalue(), out_name


def _render_result_breakdown(evaluacion: Evaluacion) -> None:
    st.markdown(f"**Resumen general:** {evaluacion.resumen_general}")

    rows = [
        {
            "Criterio": c.nombre_criterio,
            "Puntaje": f"{c.puntaje_obtenido:g} / {c.puntaje_maximo:g}",
            "Completitud": c.grado_completitud,
            "Feedback": c.feedback,
        }
        for c in evaluacion.criterios
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)

    col_a, col_b = st.columns(2)
    col_a.metric("Puntaje total", f"{evaluacion.puntaje_total:g} / {evaluacion.puntaje_maximo_total:g}")
    col_b.metric("Nota sugerida", f"{evaluacion.nota_sugerida:.1f}")


def _render_student_row(curso: str, auxiliar: str, estudiante: str, rubrica_texto: str, config: dict) -> None:
    key = _correction_key(curso, auxiliar, estudiante)
    corrections = st.session_state.setdefault("correcciones", {})

    with st.expander(estudiante, expanded=False):
        uploaded_files = st.file_uploader(
            "Archivos de la entrega (documento .pdf/.docx y, si corresponde, planilla .csv/.xlsx)",
            type=["pdf", "docx", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
            key=f"upload::{key}",
            help="Puedes adjuntar más de un archivo: por ejemplo, el informe en PDF/Word "
            "y la planilla con la base de datos de contactos en Excel/CSV.",
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            corregir_disabled = not uploaded_files or not config["api_key"] or not rubrica_texto.strip()
            if st.button("🚀 Corregir con IA", key=f"btn_corregir::{key}", disabled=corregir_disabled):
                with st.spinner(f"Corrigiendo entrega de {estudiante}..."):
                    try:
                        evaluacion, docx_bytes, docx_name = _process_multi_submission(
                            uploaded_files, estudiante, rubrica_texto, config
                        )
                        corrections[key] = {
                            "evaluacion": evaluacion,
                            "docx_bytes": docx_bytes,
                            "docx_name": docx_name,
                            "estudiante": estudiante,
                        }
                        st.success("Corrección generada correctamente.")
                    except (UnsupportedFileTypeError, FileExtractionError, EvaluationError) as exc:
                        st.error(f"No se pudo corregir la entrega: {exc}")
                    except Exception as exc:  # noqa: BLE001 - no debe romper la UI
                        st.error(f"Error inesperado: {exc}")

        resultado = corrections.get(key)

        with col2:
            if resultado is not None:
                st.download_button(
                    "⬇️ Descargar corrección",
                    data=resultado["docx_bytes"],
                    file_name=resultado["docx_name"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download::{key}",
                )

        if resultado is not None:
            st.divider()
            _render_result_breakdown(resultado["evaluacion"])


def _render_course_flow(rubrica_texto: str, config: dict) -> None:
    with st.container(key="course_card"):
        st.subheader("🎓 Selección de Curso y Auxiliar")

        cursos = list(COURSES.keys())
        curso = st.selectbox("Curso", options=cursos, key="curso_seleccionado")

        auxiliares = list(COURSES.get(curso, {}).keys())
        auxiliar = st.selectbox("Auxiliar", options=auxiliares, key="auxiliar_seleccionado")

        if not auxiliar:
            st.info("Este curso no tiene auxiliares asignados.")
            return

        estudiantes = COURSES[curso][auxiliar]

        st.markdown(f"**{len(estudiantes)} estudiante(s)** a cargo de **{auxiliar}** en **{curso}**.")

        if not config["api_key"]:
            st.warning("Ingresa una API Key en el panel lateral para poder ejecutar correcciones.")
        if not rubrica_texto.strip():
            st.warning("Define una rúbrica activa para poder ejecutar correcciones.")

    for estudiante in estudiantes:
        _render_student_row(curso, auxiliar, estudiante, rubrica_texto, config)

    corrections = st.session_state.get("correcciones", {})
    claves_auxiliar = [_correction_key(curso, auxiliar, e) for e in estudiantes]
    disponibles = [corrections[k] for k in claves_auxiliar if k in corrections]

    with st.container(key="batch_card"):
        st.subheader("📦 Descarga en Lote")
        if not disponibles:
            st.caption("Aún no hay correcciones generadas para este auxiliar.")
        else:
            st.caption(f"{len(disponibles)} de {len(estudiantes)} entregas corregidas y listas para descargar.")

            buffer_zip = _build_zip_from_corrections(disponibles)
            st.download_button(
                "⬇️ Descargar todas las correcciones (.zip)",
                data=buffer_zip,
                file_name=f"Correcciones_{auxiliar.replace(' ', '_')}.zip",
                mime="application/zip",
                type="primary",
                key=f"zip_download::{curso}::{auxiliar}",
            )


def _build_zip_from_corrections(items: list[dict]) -> bytes:
    temp_dir = Path(tempfile.mkdtemp(prefix="zip_lote_"))
    zip_path = temp_dir / "correcciones.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                zf.writestr(item["docx_name"], item["docx_bytes"])
        return zip_path.read_bytes()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Flujo 2: corrección masiva por ZIP de entregas
# ---------------------------------------------------------------------------

def _render_batch_flow(rubrica_texto: str, config: dict) -> None:
    with st.container(key="zip_card"):
        st.subheader("📦 Entregas de Estudiantes (ZIP)")
        uploaded_zip = st.file_uploader(
            "Sube un archivo .zip con las entregas (.pdf / .docx)", type=["zip"], key="zip_uploader"
        )

        procesar = st.button(
            "🚀 Corregir Entregas", type="primary", disabled=uploaded_zip is None, key="btn_procesar_zip"
        )

    if procesar:
        if not config["api_key"]:
            st.error("Debes ingresar una API Key válida en el panel lateral.")
            return
        if not rubrica_texto.strip():
            st.error("Debes definir una rúbrica antes de procesar las entregas.")
            return

        _run_batch(uploaded_zip, rubrica_texto, config)


def _run_batch(uploaded_zip, rubrica_texto: str, config: dict) -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="corrector_"))
    output_zip_path = temp_dir / "feedbacks.zip"

    try:
        with st.spinner("Descomprimiendo entregas..."):
            archivos = _extract_zip(uploaded_zip, temp_dir)

        if not archivos:
            st.warning("El ZIP no contiene archivos .pdf o .docx válidos.")
            return

        total = len(archivos)
        st.info(f"Se encontraron {total} entregas para corregir.")

        progress_bar = st.progress(0.0)
        status_text = st.empty()
        results_container = st.container()

        exitos = 0
        fallos = 0

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as out_zip:
            for i, archivo in enumerate(archivos, start=1):
                status_text.text(f"Procesando entrega {i} de {total}: {archivo.name}")

                try:
                    extraido = extract_text(archivo)

                    evaluacion = evaluar_entrega(
                        provider=config["provider"],
                        api_key=config["api_key"],
                        model=config["model"],
                        rubrica=rubrica_texto,
                        filename=extraido.filename,
                        contenido=extraido.text,
                        escala_min=config["escala_min"],
                        escala_max=config["escala_max"],
                    )

                    docx_buffer = generar_docx_feedback(evaluacion, archivo.name)
                    out_name = feedback_filename(archivo.name)
                    out_zip.writestr(out_name, docx_buffer.getvalue())

                    exitos += 1
                    with results_container:
                        st.success(f"✅ {archivo.name} → nota sugerida: {evaluacion.nota_sugerida:.1f}")

                except (UnsupportedFileTypeError, FileExtractionError, EvaluationError) as exc:
                    fallos += 1
                    with results_container:
                        st.error(f"❌ {archivo.name}: {exc}")
                except Exception as exc:  # noqa: BLE001 - no debe detener el lote completo
                    fallos += 1
                    with results_container:
                        st.error(f"❌ {archivo.name}: error inesperado ({exc})")

                progress_bar.progress(i / total)

        status_text.text(f"Proceso finalizado: {exitos} corregidas, {fallos} con error.")

        if exitos > 0:
            with open(output_zip_path, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar todos los Feedbacks (.zip)",
                    data=f.read(),
                    file_name="Feedbacks_Corregidos.zip",
                    mime="application/zip",
                    type="primary",
                    key="zip_download_batch",
                )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
