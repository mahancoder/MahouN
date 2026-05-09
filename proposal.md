# پیشنهاد عملیاتی ادغام و ارتقاء MAHOUN با New Folder

---

## ۱. لیست دقیق‌تر فایل‌های کلیدی برای ادغام

### الف) فایل‌ها و پوشه‌های منحصربه‌فرد و حیاتی New Folder (فاقد معادل در Mahoun یا بسیار پیشرفته‌تر):
- ultra_systems/graph/ultra_graph_builder.py
- ultra_systems/graph/ultra_graph_query_service.py
- ultra_systems/graph/ultra_relation_extractor.py
- ultra_systems/rag/ultra_graph_rag.py
- ultra_systems/rag/ultra_indexing_system.py
- ultra_systems/rag/ultra_evaluation_system.py
- ultra_systems/self_improve/ultra_self_improvement_system.py
- ultra_systems/self_improve/ultra_bandit_system.py
- ultra_systems/monitoring/ultra_monitoring.py
- ultra_systems/chunking/ultra_semantic_chunker.py
- ultra_systems/embedding/ultra_embedding_provider.py
- ultra_systems/caching/ultra_retrieval_cache.py
- ultra_systems/guardrails/ultra_citation_auditor.py
- ultra_systems/guardrails/ultra_nli_verifier.py
- ultra_systems/reasoning/ultra_reasoning_service.py
- ultra_systems/retrieval/ultra_hybrid_search.py
- ultra_systems/reranking/ultra_gat_reranker.py
- ultra_systems/training/ultra_lora_trainer.py
- ultra_systems/pipelines/ultra_legal_data_pipeline.py
- pipelines/active_learning/run_active_learning.py
- shadow_deployment.py
- adversarial_detector.py
- alerting.py
- monitoring/
- ... (برای لیست کامل، اسکریپت زیر را ببینید)

### ب) فایل‌هایی که در هر دو شاخه وجود دارند اما نسخه New Folder پیشرفته‌تر است:
- entity_extractor.py
- graph_builder.py
- relationship_builder.py
- ... (بررسی دقیق لازم است)

---

## ۲. ابزارهای پیشنهادی برای refactor و تست

### الف) Refactor namespace و importها:
- استفاده از ابزارهای جستجو و جایگزینی (مثل VSCode Find/Replace in Files یا PyCharm Refactor)
- اسکریپت Python برای جایگزینی خودکار:
  ```python
  import os, re
  for root, _, files in os.walk('New Folder'):
      for f in files:
          if f.endswith('.py'):
              path = os.path.join(root, f)
              with open(path, 'r', encoding='utf-8') as file:
                  content = file.read()
              # جایگزینی namespace
              content = re.sub(r'from core\.monitoring', 'from mahoun.graph.monitoring', content)
              # سایر جایگزینی‌ها...
              with open(path, 'w', encoding='utf-8') as file:
                  file.write(content)
  ```
- استفاده از ابزارهای lint و autopep8/black برای یکدست‌سازی کد پس از refactor

### ب) تست و اعتبارسنجی:
- اجرای تست‌های موجود در New Folder (`pytest New Folder/tests/`)
- اجرای تست‌های Mahoun پس از ادغام (`pytest tests/`)
- افزودن تست‌های یکپارچه برای مسیرهای بحرانی (graph, rag, monitoring, ...)

---

## ۳. برنامه‌ریزی عملیاتی ادغام

### گام ۱: آرشیو و مستندسازی
- ایجاد یک شاخه git جدید برای New Folder و ذخیره snapshot
- مستندسازی لیست فایل‌های کلیدی و قابلیت‌های منحصربه‌فرد

### گام ۲: تحلیل و دسته‌بندی
- دسته‌بندی فایل‌ها به سه گروه: فقط New Folder، مشترک (اما New Folder پیشرفته‌تر)، فقط Mahoun

### گام ۳: ادغام تدریجی (Selective Integration)
- شروع با ماژول‌های ultra_systems/graph، rag، monitoring، self_improve
- refactor namespace و importها با ابزارهای خودکار
- اجرای تست‌های یکپارچه پس از هر مرحله ادغام

### گام ۴: rollout تدریجی و مستندسازی
- مستندسازی تغییرات و آموزش تیم
- rollout تدریجی قابلیت‌های جدید در محیط staging و سپس production

---

## ۴. اسکریپت پیشنهادی برای استخراج لیست کامل فایل‌ها

```python
import os
with open('new_folder_file_list.txt', 'w', encoding='utf-8') as out:
    for root, _, files in os.walk('New Folder'):
        for f in files:
            if f.endswith('.py'):
                out.write(os.path.relpath(os.path.join(root, f), 'New Folder') + '\n')
```
- این اسکریپت لیست کامل فایل‌های پایتون را استخراج می‌کند تا برای مستندسازی و برنامه‌ریزی ادغام استفاده شود.

---

## ۵. توصیه‌های کلیدی

- حذف هیچ‌یک از قابلیت‌های پیشرفته New Folder توصیه نمی‌شود؛ حتی اگر فعلاً مورد نیاز نباشند.
- ادغام تدریجی و هدفمند با refactor namespace و تست کامل، بهترین راهکار برای ارتقاء سریع و مطمئن پلتفرم است.
- مستندسازی و آموزش تیم توسعه برای استفاده از قابلیت‌های جدید الزامی است.
- حفظ snapshot اولیه برای بازگشت در صورت نیاز ضروری است.

---

در صورت نیاز به راهنمایی بیشتر برای هر مرحله، آماده همکاری هستم.
موفق باشید!

---

## ضمیمه: لیست کامل فایل‌های پایتون New Folder

```
model_fallback.py
pii_scrubber.py
rolling_stats.py
metrics_tracker.py
__init__.py
alerting.py
wandb_logger.py
model_manager.py
shadow_deployment.py
metrics_endpoint.py
adversarial_detector.py
anomaly_detector.py
retention.py
model_reliability.py
rbac.py
diagnostic_reports.py
pipelines/extract_ner.py
pipelines/indexing.py
pipelines/extract_entities.py
pipelines/cross_encoder.py
pipelines/advanced_bart.py
pipelines/entity_linker.py
pipelines/embedding_provider.py
pipelines/lora_ner_trainer.py
pipelines/graph_build.py
pipelines/gat_trainer.py
pipelines/build_bm25.py
pipelines/lora_embedding_trainer.py
pipelines/quality_analyzer.py
pipelines/query_rewriter.py
pipelines/gnn.py
pipelines/chunker.py
pipelines/graph_analytics.py
pipelines/__init__.py
pipelines/persian_legal_nlp.py
pipelines/advanced_crf.py
pipelines/gnn_graph_builder.py
pipelines/community.py
pipelines/nli_verify.py
pipelines/validation.py
pipelines/wandb_logger.py
pipelines/utils_text.py
pipelines/run_active_learning.py
pipelines/retrieval_cache.py
pipelines/embed_index.py
pipelines/advanced_training_system.py
pipelines/ingestion_pipeline.py
pipelines/_config.py
pipelines/data_augmentation.py
pipelines/peft_manager.py
pipelines/smart_chunker.py
pipelines/metadata_validator.py
pipelines/labeling.py
pipelines/advanced_lora_trainer.py
pipelines/preprocess.py
pipelines/advanced_query_enhancement.py
pipelines/_logging.py
pipelines/monitoring.py
pipelines/gat_reranker.py
pipelines/semantic_chunker.py
pipelines/retrieve_rag.py
pipelines/eval_retrieval.py
pipelines/embedding.py
pipelines/structure_validate.py
pipelines/data_loader.py
pipelines/smart_cache.py
pipelines/expand_now.py
pipelines/labeling/__init__.py
pipelines/labeling/weight.py
pipelines/labeling/ultra_advanced_labeler.py
pipelines/labeling/combined_labeling_augmentation.py
pipelines/guardrails/__init__.py
pipelines/guardrails/hallucination_detector.py
pipelines/guardrails/citation_auditor.py
pipelines/guardrails/nli_verifier.py
pipelines/embedding/__init__.py
pipelines/embedding/service.py
pipelines/reranker/cross_encoder.py
pipelines/reranker/__init__.py
pipelines/retriever/embedding_provider.py
pipelines/retriever/__init__.py
pipelines/data_prep_advanced/indexing.py
pipelines/data_prep_advanced/entity_linker.py
pipelines/data_prep_advanced/indexing_example.py
pipelines/data_prep_advanced/pipeline_manager.py
pipelines/data_prep_advanced/cli.py
pipelines/data_prep_advanced/orchestrator.py
pipelines/data_prep_advanced/quality_analyzer.py
pipelines/data_prep_advanced/ingestion.py
pipelines/data_prep_advanced/pipeline.py
pipelines/data_prep_advanced/__init__.py
pipelines/data_prep_advanced/validation.py
pipelines/data_prep_advanced/data_augmentation.py
pipelines/data_prep_advanced/smart_chunker.py
pipelines/data_prep_advanced/test_indexing.py
pipelines/data_prep_advanced/labeling.py
pipelines/data_prep_advanced/config.py
pipelines/data_prep_advanced/monitoring.py
pipelines/data_prep_advanced/preprocessing.py
pipelines/data_prep_advanced/embedding.py
pipelines/data_prep_advanced/smart_chunker_fixed.py
pipelines/gnn/gat_trainer.py
pipelines/gnn/uncertainty_estimator.py
pipelines/gnn/graph_analytics.py
pipelines/gnn/__init__.py
pipelines/gnn/gnn_graph_builder.py
pipelines/gnn/graph_builder.py
pipelines/gnn/model_loader.py
pipelines/gnn/gat_reranker.py
pipelines/gnn/semantic_chunker.py
pipelines/training/wandb_integration.py
pipelines/training/__init__.py
pipelines/graph/__init__.py
pipelines/graph/document_citation_graph.py
pipelines/graph/graph_reranker.py
pipelines/graph/relation_extractor.py
pipelines/cache/models.py
pipelines/cache/manager.py
pipelines/cache/__init__.py
pipelines/cache/embedding_cache.py
pipelines/active_learning/__init__.py
pipelines/active_learning/run_active_learning.py
pipelines/batch/worker.py
pipelines/batch/models.py
pipelines/batch/__init__.py
pipelines/batch/queue.py
pipelines/chunking/quality_analyzer.py
pipelines/chunking/__init__.py
pipelines/chunking/service.py
pipelines/ingestion/parsers.py
pipelines/ingestion/validators.py
pipelines/ingestion/__init__.py
pipelines/ingestion/document_classifier.py
pipelines/ingestion/example_usage.py
pipelines/ingestion/data_orchestrator.py
pipelines/ingestion/auto_ingest.py
pipelines/sequence_modeling/advanced_bart.py
pipelines/sequence_modeling/__init__.py
pipelines/sequence_modeling/advanced_crf.py
pipelines/finetuning/lora_ner_trainer.py
pipelines/finetuning/lora_embedding_trainer.py
pipelines/finetuning/test_imports.py
pipelines/finetuning/__init__.py
pipelines/finetuning/prepare_training_data.py
pipelines/finetuning/example_usage.py
pipelines/finetuning/peft_manager.py
pipelines/finetuning/advanced_lora_trainer.py
pipelines/validation/__init__.py
pipelines/validation/metadata_validator.py
pipelines/vector_store/models.py
pipelines/vector_store/manager.py
pipelines/vector_store/__init__.py
pipelines/vector_store/config.py
pipelines/vector_store/interfaces.py
pipelines/vector_store/backends/base.py
pipelines/vector_store/backends/__init__.py
pipelines/vector_store/backends/faiss_backend.py
pipelines/vector_store/backends/chromadb_backend.py
orchestrator/__init__.py
orchestrator/graph_enhanced_chatbot.py
orchestrator/qa/legal_chatbot_framework.py
orchestrator/qa/__init__.py
orchestrator/qa/advanced_chatbot.py
graph/ultra_legal_data_pipeline.py
graph/relationship_builder.py
graph/ultra_relation_extractor.py
graph/__init__.py
graph/ultra_bandit_system.py
graph/entity_extractor.py
graph/ultra_graph_query_service.py
graph/analytics_service.py
graph/query_service.py
graph/batch_importer.py
graph/neo4j_adapter.py
graph/law_importer.py
graph/document_importer.py
graph/services/rag_integration.py
graph/services/__init__.py
graph/services/analytics_service.py
graph/services/query_service.py
graph/services/tests/test_rag_integration.py
graph/services/tests/__init__.py
graph/services/tests/test_advanced_analytics.py
graph/services/tests/test_advanced_query_service.py
graph/importers/__init__.py
graph/importers/batch_importer.py
graph/importers/law_importer.py
graph/importers/document_importer.py
graph/importers/tests/__init__.py
graph/importers/tests/test_importers.py
graph/security/__init__.py
graph/security/anonymization.py
graph/security/rbac.py
graph/backup/neo4j_backup.py
graph/backup/__init__.py
graph/monitoring/logging_config.py
graph/monitoring/__init__.py
graph/monitoring/metrics.py
graph/monitoring/health.py
graph/builders/entity_extractor_advanced.py
graph/builders/relationship_builder.py
graph/builders/__init__.py
graph/builders/embedding_generator.py
graph/builders/entity_extractor.py
graph/builders/graph_builder.py
graph/builders/tests/test_embedding_generator.py
graph/builders/tests/__init__.py
graph/builders/tests/test_relationship_builder.py
graph/builders/tests/test_entity_extractor.py
graph/schema/node_types.py
graph/schema/node_types_advanced.py
graph/schema/__init__.py
graph/tests/__init__.py
graph/tests/test_integration.py
graph/neo4j/query_builder.py
graph/neo4j/models.py
graph/neo4j/init_schema.py
graph/neo4j/__init__.py
graph/neo4j/connection.py
graph/neo4j/algorithms.py
graph/neo4j/operations.py
graph/neo4j/schema.py
graph/neo4j/monitoring.py
graph/neo4j/examples/import_documents.py
graph/neo4j/examples/__init__.py
graph/neo4j/examples/import_laws.py
graph/neo4j/examples/schema_setup.py
graph/neo4j/tests/test_connection.py
graph/neo4j/tests/__init__.py
graph/neo4j/tests/test_relationship_builder.py
graph/neo4j/tests/test_schema.py
graph/retrieval/__init__.py
graph/retrieval/graph_hop.py
graph/retrieval/gat_reranker.py
graph/validation/data_quality.py
graph/validation/__init__.py
graph/validation/scheduled_validation.py
graph/validation/tests/__init__.py
graph/validation/tests/test_data_quality.py
schemas/legal_struct_schema.py
schemas/__init__.py
schemas/field_labels_fa.py
schemas/text_schema.py
sdk/mahoun_client.py
sdk/vector_db_client.py
sdk/__init__.py
sdk/setup.py
sdk/examples.py
sdk/examples/vector_db_examples.py
sdk/examples/basic_usage.py
ultra_systems/__init__.py
ultra_systems/pipelines/ultra_legal_data_pipeline.py
ultra_systems/pipelines/__init__.py
ultra_systems/pipelines/ultra_data_ingestion.py
ultra_systems/guardrails/__init__.py
ultra_systems/guardrails/ultra_nli_verifier.py
ultra_systems/guardrails/ultra_citation_auditor.py
ultra_systems/embedding/ultra_embedding_provider.py
ultra_systems/embedding/__init__.py
ultra_systems/rag/ultra_indexing_system.py
ultra_systems/rag/__init__.py
ultra_systems/rag/ultra_graph_rag.py
ultra_systems/rag/ultra_training_system.py
ultra_systems/rag/ultra_evaluation_system.py
ultra_systems/reranking/__init__.py
ultra_systems/reranking/ultra_gat_reranker.py
ultra_systems/query/ultra_query_rewriter.py
ultra_systems/query/__init__.py
ultra_systems/self_improve/ultra_rl_agent.py
ultra_systems/self_improve/ultra_orchestrator_complete.py
ultra_systems/self_improve/ultra_hyperparameter_optimization.py
ultra_systems/self_improve/ultra_active_learning.py
ultra_systems/self_improve/__init__.py
ultra_systems/self_improve/ultra_active_learning_pipeline.py
ultra_systems/self_improve/ultra_bandit_system.py
ultra_systems/self_improve/ultra_causal_ab_integration.py
ultra_systems/self_improve/ultra_self_improve_integration.py
ultra_systems/self_improve/ultra_performance_monitoring.py
ultra_systems/self_improve/ultra_self_improvement_system.py
ultra_systems/training/__init__.py
ultra_systems/training/ultra_lora_trainer.py
ultra_systems/reasoning/__init__.py
ultra_systems/reasoning/ultra_reasoning_service.py
ultra_systems/monitoring/__init__.py
ultra_systems/monitoring/ultra_monitoring.py
ultra_systems/graph/ultra_relation_extractor.py
ultra_systems/graph/__init__.py
ultra_systems/graph/ultra_graph_query_service.py
ultra_systems/graph/ultra_graph_builder.py
ultra_systems/graph/ultra_gat_trainer.py
ultra_systems/core/ultra_orchestrator.py
ultra_systems/core/__init__.py
ultra_systems/nlp/ultra_persian_legal_nlp.py
ultra_systems/nlp/ultra_entity_extractor.py
ultra_systems/nlp/__init__.py
ultra_systems/chunking/__init__.py
ultra_systems/chunking/ultra_semantic_chunker.py
ultra_systems/caching/ultra_retrieval_cache.py
ultra_systems/caching/__init__.py
ultra_systems/retrieval/__init__.py
ultra_systems/retrieval/ultra_hybrid_search.py
ultra_systems/vector_store/__init__.py
ultra_systems/vector_store/ultra_chromadb_backend.py
flows/__init__.py
flows/enhanced_rag.py
```
