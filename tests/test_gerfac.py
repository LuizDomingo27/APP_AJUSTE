# -*- coding: utf-8 -*-
"""
Suíte de testes unitários para a funcionalidade GERFAC.

Testa:
1. Normalização e processamento dos dados da planilha (com aliases).
2. Tratamento de exceções para colunas obrigatórias ausentes.
3. Operações de banco de dados (gravação, leitura e metadados) usando um banco temporário.
4. Cálculo correto de métricas e KPIs.
5. Exportação da planilha Excel.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import utils.database as db
import utils.data_processor as dp


class TestGerfacFuncionalidades(unittest.TestCase):

    def setUp(self) -> None:
        # Configurar banco de dados temporário para evitar poluir o banco de produção
        self.temp_dir = tempfile.mkdtemp()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir) / "test_ajustes.db"

        # DataFrame simulando dados válidos do ERP (com variações de cabeçalhos e acentuações)
        self.mock_raw_data = pd.DataFrame({
            "Grupo": ["GERAL", "GERAL", "INTERNO"],
            "Prest. Serviço": ["OFICINA A", "OFICINA B", "OFICINA A"],
            "Agrupador": ["2026-07-01", "2026-07-01", "2026-07-01"],
            "OP": [10001, 10002, 10003],
            "Artigo": [111, 222, 333],
            "Fase": ["COST", "CORT", "COST"],
            "Sit. Atual OP": ["Concluída", "Pendente", "Concluída"],
            "Sit. OP na data": ["Recebida", "Pendente", "Recebida"],
            "Dt. Problema": ["2026-07-03", "2026-07-04", "2026-07-03"],
            "Descrição": ["Outros", "Erro", "Outros"],
            "Inf. Complementar (P. Serviço)": ["Preço incorreto", "Tempo divergente", "Preço incorreto"],
            "Sit. Problema": ["Pendente", "Pendente", "Pendente"],
            "INDICADORES": ["Corte", "Qualidade", "Corte"],
            "Dt. Fim At.": [None, None, None]
        })

    def tearDown(self) -> None:
        # Restaurar banco original e deletar temporários
        db.DB_PATH = self.original_db_path
        
        import gc
        import time
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            time.sleep(0.1)
            gc.collect()
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_gerfac_columns_success(self) -> None:
        # Testar se os aliases das colunas são resolvidos corretamente (ex: sem acento ou minúsculo)
        raw_df_diff_headers = pd.DataFrame({
            "grupo": ["G1"],
            "prest. servico": ["OFICINA X"],
            "agrupador": ["2026-07-01"],
            "op": [999],
            "artigo": [999],
            "fase": ["F1"],
            "sit. atual op": ["S1"],
            "sit. op na data": ["S2"],
            "dt. problema": ["2026-07-05"],
            "descrição": ["D1"],
            "inf. complementar (p. servico)": ["Observacao teste"],
            "sit. problema": ["P1"],
            "indicadores": ["Silk"],
        })
        normalized = dp.normalize_gerfac_columns(raw_df_diff_headers)
        self.assertIn("INDICADORES", normalized.columns)
        self.assertIn("Inf. Complementar (P. Serviço)", normalized.columns)
        self.assertIn("Dt. Problema", normalized.columns)
        self.assertIn("Prest. Serviço", normalized.columns)

    def test_normalize_gerfac_columns_missing_required(self) -> None:
        # Testar se levanta ValueError quando colunas obrigatórias estão ausentes
        invalid_raw = pd.DataFrame({
            "Grupo": ["G1"],
            # Falta Prest. Serviço, INDICADORES, etc.
        })
        with self.assertRaises(ValueError):
            dp.normalize_gerfac_columns(invalid_raw)

    def test_process_gerfac_data(self) -> None:
        # Adicionar uma linha com Dt. Problema inválida e outra com nan no Prestador
        invalid_row_1 = pd.DataFrame({
            "Grupo": ["G2"],
            "Prest. Serviço": ["OFICINA C"],
            "Agrupador": ["2026-07-01"],
            "OP": [10004],
            "Artigo": [444],
            "Fase": ["COST"],
            "Sit. Atual OP": ["Concluída"],
            "Sit. OP na data": ["Recebida"],
            "Dt. Problema": ["Data Inválida"],  # Será convertida em NaT e descartada
            "Descrição": ["Outros"],
            "Inf. Complementar (P. Serviço)": ["Erro teste"],
            "Sit. Problema": ["Pendente"],
            "INDICADORES": ["Qualidade"],
            "Dt. Fim At.": [None]
        })
        invalid_row_2 = pd.DataFrame({
            "Grupo": ["G3"],
            "Prest. Serviço": ["nan"],  # Será descartado
            "Agrupador": ["2026-07-01"],
            "OP": [10005],
            "Artigo": [555],
            "Fase": ["COST"],
            "Sit. Atual OP": ["Concluída"],
            "Sit. OP na data": ["Recebida"],
            "Dt. Problema": ["2026-07-03"],
            "Descrição": ["Outros"],
            "Inf. Complementar (P. Serviço)": ["Erro teste 2"],
            "Sit. Problema": ["Pendente"],
            "INDICADORES": ["Qualidade"],
            "Dt. Fim At.": [None]
        })
        
        full_raw = pd.concat([self.mock_raw_data, invalid_row_1, invalid_row_2], ignore_index=True)
        processed = dp.process_gerfac_data(full_raw)
        
        # O DataFrame original tinha 3 linhas válidas, as outras duas devem ser descartadas
        self.assertEqual(len(processed), 3)
        self.assertFalse(processed["Dt. Problema"].isna().any())
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(processed["Dt. Problema"]))

    def test_database_persistence_and_metadata(self) -> None:
        processed = dp.process_gerfac_data(self.mock_raw_data)
        
        # Testar gravação
        db.save_gerfac_to_db(processed)
        self.assertTrue(db.DB_PATH.exists())

        # Testar metadados
        info = db.get_db_info_gerfac()
        self.assertIsNotNone(info)
        self.assertEqual(info["count"], 3)
        self.assertIn("upload_date", info)

        # Testar carregamento
        loaded = db.load_gerfac_from_db()
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 3)
        # Verificar se as colunas de data foram devidamente convertidas para Datetime
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(loaded["Dt. Problema"]))

    def test_build_gerfac_metrics(self) -> None:
        processed = dp.process_gerfac_data(self.mock_raw_data)
        metrics = dp.build_gerfac_metrics(processed)

        # Total de chamados
        self.assertEqual(metrics.total_chamados, 3)

        # Principal Motivo: "Preço incorreto" aparece 2 vezes, "Tempo divergente" 1 vez.
        self.assertEqual(metrics.motivo_principal, "Preço incorreto")
        self.assertEqual(metrics.motivo_principal_qtd, 2)
        # 2 de 3 = 66.7%
        self.assertAlmostEqual(metrics.motivo_principal_pct, 66.7, places=1)

        # Setor com Mais Problema: "Corte" aparece 2 vezes, "Qualidade" 1 vez.
        self.assertEqual(metrics.setor_principal, "Corte")
        self.assertEqual(metrics.setor_principal_qtd, 2)
        # 2 de 3 = 66.7%
        self.assertAlmostEqual(metrics.setor_principal_pct, 66.7, places=1)

        # Oficinas resumo
        oficinas_qtds = dict(zip(metrics.oficinas_resumo["OFICINA"], metrics.oficinas_resumo["QTD"]))
        self.assertEqual(oficinas_qtds["OFICINA A"], 2)
        self.assertEqual(oficinas_qtds["OFICINA B"], 1)

    def test_export_gerfac_excel(self) -> None:
        processed = dp.process_gerfac_data(self.mock_raw_data)
        excel_bytes = dp.export_gerfac_excel(processed, "03/07/2026", "04/07/2026")
        
        self.assertIsInstance(excel_bytes, bytes)
        self.assertGreater(len(excel_bytes), 0)


if __name__ == "__main__":
    unittest.main()
