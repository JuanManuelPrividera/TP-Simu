import csv
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from generar_tabla_combinaciones import construir_filas, escribir_csv  # noqa: E402


class PruebasTablaCombinaciones(unittest.TestCase):
    def setUp(self):
        self.definicion = {
            "cases": [{
                "case_id": "fifo_cm_i1_e2_q3_em4",
                "description": "Caso de prueba",
                "ALG": "FIFO",
                "CM": [1, 2, 3, 4],
            }]
        }
        self.salida = {
            "casos": [{
                "case_id": "fifo_cm_i1_e2_q3_em4",
                "resultados": {
                    "CostoPromLote": 12.5,
                    "TiempoParadoEtapa": {"impresion": 10, "qa": 20},
                },
            }]
        }

    def test_aplana_metricas_y_agrega_la_configuracion(self):
        fila = construir_filas(self.definicion, self.salida)[0]
        self.assertEqual(fila["algoritmo"], "FIFO")
        self.assertEqual(fila["maquinas_encuadernacion"], 2)
        self.assertEqual(fila["TiempoParadoEtapa.impresion"], 10)
        self.assertEqual(fila["CostoPromLote"], 12.5)

    def test_escribe_csv_con_punto_y_coma(self):
        filas = construir_filas(self.definicion, self.salida)
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "tabla.csv"
            escribir_csv(filas, ruta)
            with ruta.open(encoding="utf-8-sig", newline="") as archivo:
                datos = list(csv.DictReader(archivo, delimiter=";"))
        self.assertEqual(datos[0]["case_id"], "fifo_cm_i1_e2_q3_em4")
        self.assertEqual(datos[0]["TiempoParadoEtapa.qa"], "20")

    def test_rechaza_resultados_faltantes(self):
        with self.assertRaisesRegex(ValueError, "Falta el resultado"):
            construir_filas(self.definicion, {"casos": []})


if __name__ == "__main__":
    unittest.main()
