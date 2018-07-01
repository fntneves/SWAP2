excesso=10 
export excesso

pedidoReal: pedidoTeste.py
	make input excesso=$(excesso)
	python pedidoTeste.py 0

pedidoTeste: pedidoTeste.py
	python pedidoTeste.py test
 
input: juntarJsons.py Data/alunosSwap.json Data/horario_com_teoricas.json Data/grupos.json
	python juntarJsons.py Data/alunosSwap.json Data/horario_com_teoricas.json Data/grupos.json $(excesso)
