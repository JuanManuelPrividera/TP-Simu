from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from simulacion import cargar_json  # noqa: E402


class PruebasCasosCombinatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        definicion = cargar_json(
            SCRIPTS / "config" / "casos" / "combinaciones_maquinas_algoritmos.json"
        )
        cls.casos = definicion["cases"]

    def test_genera_las_30000_combinaciones(self):
        self.assertEqual(len(self.casos), 10**4 * 3)
        self.assertEqual(len({caso["case_id"] for caso in self.casos}), len(self.casos))

    def test_cubre_todas_las_cantidades_y_algoritmos(self):
        combinaciones = {
            (caso["ALG"], *caso["CM"])
            for caso in self.casos
        }
        self.assertIn(("FIFO", 1, 1, 1, 1), combinaciones)
        self.assertIn(("PRIORIDADES", 10, 10, 10, 10), combinaciones)
        self.assertIn(("POR_CONFIGURACION", 1, 10, 4, 7), combinaciones)

    def test_configuraciones_iniciales_coinciden_con_cm(self):
        for caso in self.casos:
            self.assertEqual(
                [len(configuraciones) for configuraciones in caso["configuraciones_iniciales"]],
                caso["CM"],
            )


if __name__ == "__main__":
    unittest.main()
