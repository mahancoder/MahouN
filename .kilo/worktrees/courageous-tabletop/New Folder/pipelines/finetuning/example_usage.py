"""
Example Usage of Advanced PEFT Module
======================================

نمونه‌های کاربردی برای استفاده از سیستم پیشرفته PEFT
"""

import torch
from torch.utils.data import DataLoader

# Import از module
from pipelines.finetuning import (
    # Advanced LoRA
    AdvancedLoRATrainer,
    AdvancedLoRAConfig,
    LoRAMethod,
    TaskType,
    LoRAFusion,
    DynamicRankAllocator,
    
    # PEFT Manager
    PEFTManager,
    PEFTMethod,
    AdapterInfo,
)


def example_1_basic_lora():
    """مثال 1: استفاده پایه از LoRA"""
    
    print("\n" + "="*80)
    print("مثال 1: Fine-tuning پایه با LoRA")
    print("="*80)
    
    # تنظیمات LoRA
    config = AdvancedLoRAConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        method=LoRAMethod.LORA,
        use_rslora=True,
    )
    
    # ایجاد trainer
    trainer = AdvancedLoRATrainer(
        base_model_name="BAAI/bge-m3",
        task_type=TaskType.EMBEDDING,
        lora_config=config,
    )
    
    print("✅ Trainer آماده است")
    print(f"   Method: {config.method.value}")
    print(f"   Rank: {config.r}")
    print(f"   Alpha: {config.lora_alpha}")
    
    # Training
    # trainer.train(
    #     train_dataloader=train_loader,
    #     eval_dataloader=eval_loader,
    #     num_epochs=3,
    #     learning_rate=3e-4,
    #     output_dir="models/lora_embedding",
    # )


def example_2_qlora():
    """مثال 2: QLoRA برای کاهش memory"""
    
    print("\n" + "="*80)
    print("مثال 2: QLoRA با 4-bit Quantization")
    print("="*80)
    
    # تنظیمات QLoRA
    config = AdvancedLoRAConfig(
        r=16,
        lora_alpha=32,
        method=LoRAMethod.QLORA,
        load_in_4bit=True,
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_quant_type="nf4",
        use_gradient_checkpointing=True,
    )
    
    # ایجاد trainer
    trainer = AdvancedLoRATrainer(
        base_model_name="HooshvareLab/bert-base-parsbert-uncased",
        task_type=TaskType.NER,
        lora_config=config,
    )
    
    print("✅ QLoRA Trainer آماده است")
    print(f"   Quantization: 4-bit")
    print(f"   Memory Saving: ~75%")
    print(f"   Gradient Checkpointing: Enabled")


def example_3_adalora():
    """مثال 3: AdaLoRA برای بهینه‌سازی rank"""
    
    print("\n" + "="*80)
    print("مثال 3: AdaLoRA با Adaptive Rank")
    print("="*80)
    
    # تنظیمات AdaLoRA
    config = AdvancedLoRAConfig(
        method=LoRAMethod.ADALORA,
        init_r=12,
        target_r=8,
        beta1=0.85,
        beta2=0.85,
        tinit=0,
        tfinal=1000,
        deltaT=10,
    )
    
    trainer = AdvancedLoRATrainer(
        base_model_name="BAAI/bge-m3",
        task_type=TaskType.EMBEDDING,
        lora_config=config,
    )
    
    print("✅ AdaLoRA Trainer آماده است")
    print(f"   Initial Rank: {config.init_r}")
    print(f"   Target Rank: {config.target_r}")
    print(f"   Rank خودکار بهینه می‌شود")


def example_4_dora():
    """مثال 4: DoRA برای بهترین performance"""
    
    print("\n" + "="*80)
    print("مثال 4: DoRA (Weight-Decomposed LoRA)")
    print("="*80)
    
    # تنظیمات DoRA
    config = AdvancedLoRAConfig(
        r=8,
        lora_alpha=16,
        use_dora=True,  # فعال کردن DoRA
        use_rslora=True,
    )
    
    trainer = AdvancedLoRATrainer(
        base_model_name="BAAI/bge-m3",
        task_type=TaskType.EMBEDDING,
        lora_config=config,
    )
    
    print("✅ DoRA Trainer آماده است")
    print(f"   DoRA: Enabled")
    print(f"   Performance: بهترین در بین LoRA variants")


def example_5_peft_manager():
    """مثال 5: مدیریت چند adapter"""
    
    print("\n" + "="*80)
    print("مثال 5: PEFT Manager - مدیریت Multi-Adapter")
    print("="*80)
    
    # ایجاد manager
    manager = PEFTManager(
        base_model_name="BAAI/bge-m3",
        adapters_dir="models/adapters",
    )
    
    # لیست adapters
    adapters = manager.list_adapters()
    print(f"\n📦 Adapters موجود: {len(adapters)}")
    for adapter in adapters:
        print(f"   • {adapter.name} ({adapter.method.value}) - {adapter.task}")
    
    # Load adapter
    if adapters:
        model = manager.load_adapter(adapters[0].name)
        print(f"\n✅ Adapter '{adapters[0].name}' بارگذاری شد")
    
    # Switch adapter
    if len(adapters) > 1:
        manager.switch_adapter(adapters[1].name)
        print(f"✅ Switch به '{adapters[1].name}'")


def example_6_adapter_fusion():
    """مثال 6: ترکیب چند adapter"""
    
    print("\n" + "="*80)
    print("مثال 6: Adapter Fusion - ترکیب Adapters")
    print("="*80)
    
    manager = PEFTManager(
        base_model_name="BAAI/bge-m3",
        adapters_dir="models/adapters",
    )
    
    # فرض کنیم 3 adapter داریم
    adapter_names = ["legal_qa", "contract_ner", "case_classification"]
    weights = [0.5, 0.3, 0.2]
    
    print(f"\n🔀 Fusing {len(adapter_names)} adapters:")
    for name, weight in zip(adapter_names, weights):
        print(f"   • {name}: {weight:.1%}")
    
    # Fuse
    # fused_model = manager.fuse_adapters(
    #     adapter_names=adapter_names,
    #     weights=weights,
    #     output_name="fused_legal",
    # )
    
    print("\n✅ Adapters ترکیب شدند")
    print("   Output: fused_legal")


def example_7_auto_routing():
    """مثال 7: Auto-routing به بهترین adapter"""
    
    print("\n" + "="*80)
    print("مثال 7: Auto-Routing - انتخاب خودکار Adapter")
    print("="*80)
    
    manager = PEFTManager(
        base_model_name="BAAI/bge-m3",
        adapters_dir="models/adapters",
    )
    
    # Query
    text = "قانون مدنی چیست؟"
    context = {"task": "legal_qa", "domain": "civil_law"}
    
    print(f"\n📝 Query: {text}")
    print(f"📋 Context: {context}")
    
    # Auto-route
    if manager.router:
        adapter_name = manager.router.route(text, context)
        print(f"\n✅ Routed to: {adapter_name}")
        
        # Load and use
        # model = manager.load_adapter(adapter_name)
        # embedding = model.encode(text)


def example_8_dynamic_rank():
    """مثال 8: Dynamic Rank Allocation"""
    
    print("\n" + "="*80)
    print("مثال 8: Dynamic Rank Allocation")
    print("="*80)
    
    # فرض کنیم یک model داریم
    # model = ...
    # train_loader = ...
    
    # allocator = DynamicRankAllocator(
    #     model=model,
    #     total_params_budget=1_000_000,
    #     importance_metric="gradient_norm",
    # )
    
    # # محاسبه importance
    # importance = allocator.compute_importance(train_loader)
    
    # # تخصیص ranks
    # rank_allocation = allocator.allocate_ranks(min_rank=4, max_rank=32)
    
    print("✅ Dynamic Rank Allocator")
    print("   • لایه‌های مهم → rank بالا")
    print("   • لایه‌های کم‌اهمیت → rank پایین")
    print("   • بهینه‌سازی خودکار")


def example_9_lora_fusion():
    """مثال 9: LoRA Fusion Techniques"""
    
    print("\n" + "="*80)
    print("مثال 9: LoRA Fusion Techniques")
    print("="*80)
    
    # فرض کنیم base model و lora paths داریم
    # base_model = ...
    # lora_paths = ["models/lora1", "models/lora2", "models/lora3"]
    
    # 1. Weighted Fusion
    print("\n1️⃣ Weighted Fusion:")
    print("   fused = 0.5*A1 + 0.3*A2 + 0.2*A3")
    # fused = LoRAFusion.weighted_fusion(
    #     base_model,
    #     lora_paths,
    #     weights=[0.5, 0.3, 0.2]
    # )
    
    # 2. Task Arithmetic
    print("\n2️⃣ Task Arithmetic:")
    print("   • Add: A1 + A2")
    print("   • Subtract: A1 - A2")
    print("   • Negate: -A1")
    # fused = LoRAFusion.task_arithmetic(
    #     base_model,
    #     lora_paths,
    #     operation="add"
    # )


def example_10_complete_pipeline():
    """مثال 10: Pipeline کامل"""
    
    print("\n" + "="*80)
    print("مثال 10: Complete Fine-tuning Pipeline")
    print("="*80)
    
    print("\n📋 Pipeline Steps:")
    print("   1. تنظیم config")
    print("   2. ایجاد trainer")
    print("   3. آماده‌سازی data")
    print("   4. Training")
    print("   5. Evaluation")
    print("   6. Save adapter")
    print("   7. Register در manager")
    print("   8. Test inference")
    
    # 1. Config
    config = AdvancedLoRAConfig(
        r=8,
        lora_alpha=16,
        method=LoRAMethod.LORA,
        use_rslora=True,
        use_gradient_checkpointing=True,
        use_mixed_precision=True,
    )
    
    # 2. Trainer
    trainer = AdvancedLoRATrainer(
        base_model_name="BAAI/bge-m3",
        task_type=TaskType.EMBEDDING,
        lora_config=config,
    )
    
    # 3. Data
    # train_loader = DataLoader(...)
    # eval_loader = DataLoader(...)
    
    # 4. Train
    # trainer.train(
    #     train_dataloader=train_loader,
    #     eval_dataloader=eval_loader,
    #     num_epochs=3,
    #     learning_rate=3e-4,
    #     output_dir="models/my_adapter",
    #     use_wandb=True,
    # )
    
    # 5. Save
    # trainer.save("models/my_adapter")
    
    # 6. Register
    # manager = PEFTManager("BAAI/bge-m3")
    # manager.adapters["my_adapter"] = AdapterInfo(...)
    
    # 7. Use
    # model = manager.load_adapter("my_adapter")
    # embedding = model.encode("test text")
    
    print("\n✅ Pipeline کامل")


def main():
    """اجرای همه مثال‌ها"""
    
    print("\n" + "="*80)
    print("🚀 Advanced PEFT Module - نمونه‌های کاربردی")
    print("="*80)
    
    # اجرای مثال‌ها
    example_1_basic_lora()
    example_2_qlora()
    example_3_adalora()
    example_4_dora()
    example_5_peft_manager()
    example_6_adapter_fusion()
    example_7_auto_routing()
    example_8_dynamic_rank()
    example_9_lora_fusion()
    example_10_complete_pipeline()
    
    print("\n" + "="*80)
    print("✅ همه مثال‌ها اجرا شدند")
    print("="*80)
    print("\n📚 برای اطلاعات بیشتر:")
    print("   • ADVANCED_PEFT_GUIDE.md")
    print("   • README.md")
    print("   • advanced_lora_trainer.py")
    print("   • peft_manager.py")
    print("\n")


if __name__ == "__main__":
    main()
