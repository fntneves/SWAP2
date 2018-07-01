import json, sys, requests

if sys.argv[1] == 'test':
  alunos_json = json.load(open('Data/alunos_grupos_teste.json'))
  grupos_json = json.load(open('Data/grupos-teste.json'))
  horario_json = json.load(open('Data/horario_grupos_teste.json'))

  jsonFinal = {
    'alunos': alunos_json,
    'horario': horario_json,
    'grupos': grupos_json,
    'percentagem-excesso' : 0
  }
else:
  jsonFinal = json.load(open('Data/solverInput.json'))


# r = requests.post('http://127.0.0.1:5000/solver', json=jsonFinal)
r = requests.post('https://lei-uminho-swap2.herokuapp.com/solver', json=jsonFinal)

print r.status_code
print r.text

out_file = open('enrollments.json', 'w')
json.dump(r.json() , out_file)
