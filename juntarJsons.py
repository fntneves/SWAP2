import json, sys, requests

alunos_json  = json.load(open(sys.argv[1]))
horario_json = json.load(open(sys.argv[2]))
grupos_json = json.load(open(sys.argv[3]))
excesso = sys.argv[4]

jsonFinal = {
  'alunos': alunos_json,
  'horario': horario_json,
  'grupos': grupos_json,
  'percentagem-excesso' : excesso
}

solver_input_file = open('solverInput.json', 'w')
json.dump(jsonFinal, solver_input_file)
