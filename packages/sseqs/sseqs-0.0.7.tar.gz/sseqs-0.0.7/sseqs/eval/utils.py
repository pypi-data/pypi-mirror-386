try: 
    from pytorch_lightning import seed_everything
    from boltz.data.module.inferencev2 import Boltz2InferenceDataModule
    from boltz.data.types import Manifest
    from boltz.data.write.writer import BoltzWriter
    from boltz.main import * 
except: 
    pass

import os 
import torch
from typing import Literal, Optional
from rdkit import Chem
from pathlib import Path
import json, pandas as pd 

def f2d(file):
    f = str(file)
    seed = int(f.split('_model_')[-1].replace('.json', ''))
    pdb = f.split('confidence_')[-1].split('_model')[0]
    return {'pdb': pdb, 'seed': seed} | json.loads(file.open().read())

def b2d(path):
    return pd.json_normalize([f2d(file) for file in Path(path).rglob("*.json")])

def get_dataloader(data, out_dir):
    cache= "~/.boltz"
    checkpoint= None
    affinity_checkpoint= None
    devices= 1
    accelerator= "gpu"
    recycling_steps= 3
    sampling_steps: int = 200
    diffusion_samples: int = 1
    sampling_steps_affinity: int = 200
    diffusion_samples_affinity: int = 3
    max_parallel_samples: Optional[int] = None
    step_scale: Optional[float] = None
    write_full_pae: bool = False
    write_full_pde: bool = False
    output_format: Literal["pdb", "mmcif"] = "pdb" # alex: changed default to pdb 
    num_workers: int = 0
    override: bool = True
    seed: Optional[int] = None
    use_msa_server: bool = False
    msa_server_url: str = "https://api.colabfold.com"
    msa_pairing_strategy: str = "greedy"
    use_potentials: bool = False
    model: Literal["boltz1", "boltz2"] = "boltz2"
    method: Optional[str] = None
    affinity_mw_correction: Optional[bool] = False
    preprocessing_threads: int = 1
    max_msa_seqs: int = 8192
    subsample_msa: bool = True
    num_subsampled_msa: int = 1024
    no_kernels: bool = False

    torch.set_grad_enabled(False)
    torch.set_float32_matmul_precision("highest")
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    if seed is not None:
        seed_everything(seed)

    for key in ["CUEQ_DEFAULT_CONFIG", "CUEQ_DISABLE_AOT_TUNING"]: os.environ[key] = os.environ.get(key, "1")

    cache = Path(cache).expanduser()
    cache.mkdir(parents=True, exist_ok=True)

    # data 
    data = Path(data).expanduser()
    out_dir = Path(out_dir).expanduser()
    out_dir = out_dir / f"boltz_results_{data.stem}"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = check_inputs(data)
    ccd_path = cache / "ccd.pkl"
    mol_dir = cache / "mols"
    process_inputs(
        data=data,
        out_dir=out_dir,
        ccd_path=ccd_path,
        mol_dir=mol_dir,
        use_msa_server=use_msa_server,
        msa_server_url=msa_server_url,
        msa_pairing_strategy=msa_pairing_strategy,
        boltz2=model == "boltz2",
        preprocessing_threads=preprocessing_threads,
        max_msa_seqs=max_msa_seqs,)
    manifest = Manifest.load(out_dir / "processed" / "manifest.json")
    filtered_manifest = filter_inputs_structure(
        manifest=manifest,
        outdir=out_dir,
        override=override,)
    processed_dir = out_dir / "processed"
    processed = BoltzProcessedInput(
        manifest=filtered_manifest,
        targets_dir=processed_dir / "structures",
        msa_dir=processed_dir / "msa",
        constraints_dir=(
            (processed_dir / "constraints")
            if (processed_dir / "constraints").exists()
            else None
        ),
        template_dir=(
            (processed_dir / "templates")
            if (processed_dir / "templates").exists()
            else None
        ),
        extra_mols_dir=(
            (processed_dir / "mols") if (processed_dir / "mols").exists() else None
        ),)
    data_module = Boltz2InferenceDataModule(
        manifest=processed.manifest,
        target_dir=processed.targets_dir,
        msa_dir=processed.msa_dir,
        mol_dir=mol_dir,
        num_workers=num_workers,
        constraints_dir=processed.constraints_dir,
        template_dir=processed.template_dir,
        extra_mols_dir=processed.extra_mols_dir,
        override_method=method,
    )

    pred_writer = BoltzWriter(
        data_dir=processed.targets_dir,
        output_dir=out_dir / "predictions",
        output_format=output_format,
        boltz2=model == "boltz2",)

    return data_module.predict_dataloader(), pred_writer, data_module