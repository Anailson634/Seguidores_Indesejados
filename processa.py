import json

Dados_Obtido={}
black={}
with open("instagram.json", 'r', encoding="utf-8") as arq:
    Dados_Obtido=json.load(arq)
with open("Exec.json", "r", encoding="utf-8") as arq:
    black=json.load(arq)


for seg in Dados_Obtido["Seguindo"]:
    if seg in Dados_Obtido["Seguidores"] or seg in black["Execoes"]:
        continue
    else:
        black["BlackList"].append(seg)
        print(seg)

with open("Exec.json", 'w', encoding="utf-8") as arq:
    json.dump(black, arq, indent=4, ensure_ascii=False)