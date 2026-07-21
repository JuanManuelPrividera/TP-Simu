import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from FDP import EstadoLote  # noqa: E402
from simulacion import Lote, Simulacion, calcular_costo_defectos_no_detectados  # noqa: E402


class RNGFijo:
    def __init__(self, valor):
        self.valor = valor

    def random(self):
        return self.valor


class PruebasEstadoLote(unittest.TestCase):
    def test_fdp_usa_pd_como_probabilidad_de_defecto(self):
        self.assertTrue(EstadoLote.muestrear(RNGFijo(0.024), 0.025))
        self.assertFalse(EstadoLote.muestrear(RNGFijo(0.025), 0.025))


class PruebasQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configuracion_base = json.loads(
            (SCRIPTS / "config" / "caso_base.json").read_text(encoding="utf-8")
        )

    def simulacion(self):
        return Simulacion(copy.deepcopy(self.configuracion_base))

    def finalizar_qa(self, defectuoso, aqa):
        simulacion = self.simulacion()
        lote = Lote("config_1", 1, 0.0, 100, defectuoso=defectuoso)
        simulacion.maquinas[2][0].lote = lote
        simulacion.tproximo[2][0] = 10.0
        with patch("simulacion.AQA.muestrear", return_value=aqa), patch.object(
            simulacion, "enviar_a_etapa"
        ) as enviar:
            simulacion.terminar_etapa(2, 0)
        return simulacion, lote, enviar

    def test_lote_correcto_siempre_pasa_a_embalaje(self):
        simulacion, lote, enviar = self.finalizar_qa(False, 0.0)
        enviar.assert_called_once_with(3, lote)
        self.assertEqual(simulacion.reprocesados, 0)
        self.assertEqual(simulacion.defectuosos_no_detectados, 0)

    def test_pqa_multiplica_la_duracion_de_qa(self):
        simulacion = self.simulacion()
        simulacion.cfg["PQA"] = 0.25
        lote = Lote("config_1", 1, 0.0, 100)

        with patch("simulacion.DQA.muestrear", return_value=12.0):
            simulacion.iniciar_lote(2, 0, lote)

        self.assertEqual(simulacion.tproximo[2][0], 3.0)
        self.assertEqual(simulacion.tiempo_produccion_total, 3.0)
        self.assertEqual(simulacion.tiempo_produccion_etapa[2], 3.0)

    def test_defecto_detectado_se_reprocesa(self):
        simulacion, lote, enviar = self.finalizar_qa(True, 0.49)
        enviar.assert_called_once_with(0, lote)
        self.assertEqual(simulacion.reprocesados, 1)
        self.assertEqual(simulacion.defectuosos_no_detectados, 0)

    def test_defecto_no_detectado_pasa_a_embalaje(self):
        simulacion, lote, enviar = self.finalizar_qa(True, 0.50)
        enviar.assert_called_once_with(3, lote)
        self.assertEqual(simulacion.reprocesados, 0)
        self.assertEqual(simulacion.defectuosos_no_detectados, 1)

    def test_reproceso_vuelve_a_muestrear_estado_real(self):
        simulacion = self.simulacion()
        lote = Lote("config_1", 1, 0.0, 100)
        for instante, estado in ((10.0, True), (20.0, False)):
            simulacion.maquinas[0][0].lote = lote
            simulacion.tproximo[0][0] = instante
            with patch("simulacion.EstadoLote.muestrear", return_value=estado), patch.object(
                simulacion, "enviar_a_etapa"
            ) as enviar:
                simulacion.terminar_etapa(0, 0)
            self.assertIs(lote.defectuoso, estado)
            enviar.assert_called_once_with(1, lote)

    def test_penalizacion_equivale_a_tres_promedios_base(self):
        penalizacion = calcular_costo_defectos_no_detectados(1000.0, 10, 1)
        self.assertEqual(penalizacion, 300.0)
        self.assertEqual((1000.0 + penalizacion) / 10, 130.0)

    def test_rechaza_configuracion_que_no_puede_terminar(self):
        configuracion = copy.deepcopy(self.configuracion_base)
        configuracion["PD"] = configuracion["PQA"] = 1.0
        with self.assertRaisesRegex(ValueError, "indefinidamente"):
            Simulacion(configuracion)

    def test_valida_rangos_de_pd_y_pqa(self):
        for parametro, valor in (("PD", -0.01), ("PD", 1.01), ("PQA", -0.01), ("PQA", 1.01)):
            with self.subTest(parametro=parametro, valor=valor):
                configuracion = copy.deepcopy(self.configuracion_base)
                configuracion[parametro] = valor
                with self.assertRaisesRegex(ValueError, parametro):
                    Simulacion(configuracion)


if __name__ == "__main__":
    unittest.main()
