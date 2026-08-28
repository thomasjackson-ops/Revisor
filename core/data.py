"""Datos mockeados de cursos, auxiliares y estudiantes asignados.

En una futura iteración esto podría reemplazarse por una fuente real
(base de datos, planilla, API institucional, etc.) sin tocar la UI,
ya que app.py solo consume la estructura COURSES.
"""

from __future__ import annotations

COURSES: dict[str, dict[str, list[str]]] = {
    "Módulo Interdisciplinario": {
        "Dominique Gajardo": [
            "Águila Altamirano, Tomás Martín",
            "Artica Santos, Aryana Avigail",
            "Moya Aguirre, Joaquin Alejandro",
            "Pérez Pérez, Belén Antonia",
        ],
        "Thomas Jackson": [
            "Burgos Jara, Sofía Valentina",
            "Caldentey Casanova, Santiago Ernesto",
            "Candia Sepúlveda, Vania Rayen",
            "Castro Gallardo, Agustin Enrique",
        ],
        "Diego Navarrete": [
            "Cisternas Hormazábal, Agustin Eugenio",
            "Cornejo Andino, Alonso Cristobal",
            "Daille Bass, Uri",
            "Iturrieta Jaque, Benjamin Nicolas",
            "Kanda Pérez, Kenzo Matias",
        ],
        "Benjamín del Pino": [
            "Espinoza Pilcol, Esteban Alejandro",
            "Fuentes Román, Martín",
            "García Uribe, Simón Andrés",
            "Gatica Ulloa, Ariel Hernán",
            "Graf De Solminihac, Sara",
            "Grunewald Carrasco, Rafaella Isabel",
            "Hernández Rosales, Renato Bastián",
            "Lagos Venegas, Martina Antonella",
            "López Pino, Agustin Sebastian",
            "Marchant Espinoza, Tomás Antonio",
            "Márquez Shipley, Sebastián Ignacio",
            "Montecinos Riffo, José Javier",
            "Moreno Muñoz, Benjamín Alejandro",
            "Ugaz Flores, Angel Jesús",
        ],
        "Marcela Pérez": [
            "Muñoz Lagos, Alejandro Esteban",
            "Noches Zumelzo, Benjamín Patricio",
            "Puga Casas, Agustina Ignacia",
            "Quispe Leon, Giancarlo de Jesus",
            "Ríos Muñoz, Magdalena Antonia",
            "Rivera Espinosa, Fernanda Andrea",
            "Riveros León, Tomás Elías",
            "Salin Julian, Claudio Eduardo",
            "Santis Vargas, Matías Felipe",
            "Sepúlveda Alvarado, Juan Sebastián",
            "Valenzuela Guerra, Bastián Alonso",
            "Vargas Ávila, Constanza Jesus",
            "Vargas Vidal, Julián Maximiliano",
            "Vásquez Muñoz, Javier Ignacio",
        ],
    },
    "Proyectos 1": {
        "Dominique Gajardo": [
            "Acevedo Núñez, José Tomás",
            "Álvarez de Araya Picero, Alonso Rafael",
            "Arriagada González, Felipe Andrés",
            "Barrera Cortés, Daniel Ignacio",
            "Cepeda Carrasco, Vicente",
            "Moreno Olaya, Andres Felipe",
        ],
        "Diego Navarrete": [
            "Berdichewsky García, Ian Andrei",
            "Maomed Abarca, Fernando Moises",
            "Montenegro Mansilla, Rafaela Alejandra",
            "Jara Silva, Valentina Ignacia",
            "Orquera Rivera, Catalina Ignacia",
        ],
        "Thomas Jackson": [
            "Vega Zúñiga, Fernanda Paz",
            "Villa Venegas, Fernanda Francesca",
        ],
    },
}
