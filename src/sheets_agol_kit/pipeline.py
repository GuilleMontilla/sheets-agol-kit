"""Pipeline de sincronizacion: respuestas crudas -> pestana limpia.

La libreria pone la mecanica (leer, iterar, escribir); el proyecto pone la
logica de cada fila via el callback build_row.
"""

from .sheets import read_responses, write_rows


def sync(spreadsheet, *, responses_tab, output_tab, headers, build_row):
    """Lee la pestana de respuestas y reescribe la pestana de salida.

    Args:
        spreadsheet: objeto de open_spreadsheet().
        responses_tab: pestana donde el Form guarda las respuestas (solo lectura).
        output_tab: pestana limpia que se reescribe completa.
        headers: encabezados de la pestana de salida.
        build_row: funcion(respuesta_dict) -> lista de valores o None para
            omitir esa respuesta (ej. si no se pudo geocodificar).

    Devuelve (filas_escritas, respuestas_totales).
    """
    responses = read_responses(spreadsheet, responses_tab)
    rows = [row for row in (build_row(r) for r in responses) if row is not None]
    write_rows(spreadsheet, output_tab, headers, rows)
    return len(rows), len(responses)
