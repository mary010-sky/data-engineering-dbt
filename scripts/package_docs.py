from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
out=root/'site/dbt';out.mkdir(parents=True,exist_ok=True)
for name in ['index.html','manifest.json','catalog.json']:
    shutil.copy2(root/'target'/name,out/name)
print('Packaged dbt documentation in site/dbt/')
