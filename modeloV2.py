# coding=utf-8
import sys, json, pprint, time
from ortools.linear_solver import pywraplp



solver = pywraplp.Solver("schedule_shifts", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

alunos_json  = json.load(open(sys.argv[1]))
horario_json = json.load(open(sys.argv[2]))
grupos_json = json.load(open('Data/grupos.json'))

suf_teoria = '-T'



alunos = {}
slots = {}
presencas = {}
gruposCompletos = {}

# Carrega alunos e as ucs em que estao inscritos para o dicionario alunos {"A82382:[Hxxxxxx,Hxxxxx]"}
for al in alunos_json:
    if len(alunos) == int(sys.argv[3]):
        break
    if al in alunos:
        print 'Aluno %s repetido' % al
    for uc in alunos_json[al]:
        if al not in alunos:
            alunos[al] = [uc]
        else:
            alunos[al] += [uc]


n_dia = 0

dias_slots = {}

#Carrega o horario e preenche os dicionarios slots, slots --> {Hxxxx:{TPX:[(Dia,Hora,Slots_1h,Capacidade)]}}}
for elem in horario_json:
    maximo_slot = 0
    for dia in elem:
        for uc in elem[dia]:
            for codigo in uc:
                horaI = uc[codigo]['HoraI']
                horaF = uc[codigo]['HoraF']
                maximo_slot = max(horaF,maximo_slot)
                # parte do codigo que adiciona o codigo-T para cadeiras com teoricas do aluno
                if codigo[-2:] == suf_teoria:
                    codigoAux = codigo[:6]
                    for al in alunos:
                        if codigoAux in alunos[al] and codigo not in alunos[al]:
                            alunos[al] += [codigo]
                if codigo[:6] == 'ALMOCO':
                    for al in alunos:
                        if codigo not in alunos[al]:
                            alunos[al] += [codigo]                        
                if codigo not in slots:
                    slots[codigo] = {}
                turno = uc[codigo]['Turno']
                if turno not in slots[codigo]:
                    slots[codigo][turno] = [(n_dia,horaI,horaF, uc[codigo]['Capacidade'] )]
                else:
                    slots[codigo][turno] += [(n_dia,horaI,horaF, uc[codigo]['Capacidade'] )]
        if n_dia not in dias_slots:
            dias_slots[n_dia] = maximo_slot
    n_dia += 1
maximo_dia = n_dia
# print('alunos:')
# pprint.pprint(alunos)
# print('ucs e slots:')
# pprint.pprint(slots)

n_al = 0
n_uc = 0
n_turno = 0
max_nr = len(alunos) * 15 * 10

for al in alunos:
    n_al += 1
    if al not in presencas:
        presencas[al] = {}
    for uc in alunos[al]:
        n_uc += 1
        if uc in slots:
            if uc not in presencas[al]:
                presencas[al][uc] = {}
            for turno in slots[uc]:
                n_turno += 1
                # presencas[al][uc][turno] = solver.BoolVar()
                presencas[al][uc][turno] = solver.IntVar(0,1,"p_%s_%s_%s" % (n_al,n_uc,n_turno))

n_uc2 = 0
n_grupo = 0
n_turno = 0
for uc in grupos_json:
    if uc not in gruposCompletos:
        gruposCompletos[uc] = {}
        n_uc2 += 1
    for grupo in grupos_json[uc]:
        n_grupo += 1
        if grupo not in gruposCompletos[uc]:
            gruposCompletos[uc][grupo] = {}
            for turno in slots[uc]:
                n_turno += 1
                gruposCompletos[uc][grupo][turno] = solver.IntVar(0,1,"g_%s_%s_%s" % (n_uc2, n_grupo, n_turno))

##################### RESTRICOES ######################################

#- Um aluno so pode ser atribuido a um e um so turno se for TP

for al in presencas:
    for uc in presencas[al]:
        if uc[-2:] != suf_teoria:
            solver.Add(solver.Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) == 1)

#- Um aluno so pode ser atribuido a so turno se for T, nao sendo obrigatório
for al in presencas:
    for uc in presencas[al]:
        if uc[-2:] == suf_teoria:
            solver.Add(solver.Sum([ presencas[al][uc][turno] for turno in presencas[al][uc]]) <= 1)

#- O numero de alocacoes para turno nao pode execeder a capacidade do mesmo

lista_capacidades = {}
for al in presencas:
    for uc in presencas[al]:
        if uc not in lista_capacidades:
            lista_capacidades[uc] = {}
        for turno in presencas[al][uc]:
            if turno not in lista_capacidades[uc]:
                lista_capacidades[uc][turno] = [ presencas[al][uc][turno] ]
            else:
                lista_capacidades[uc][turno] += [ presencas[al][uc][turno] ]
### TPS ####
for uc in lista_capacidades:
    for turno in lista_capacidades[uc]:
        if uc[-2:] != suf_teoria:
            maior = 0
            for i in range(len(slots[uc][turno])):
                maior = max(slots[uc][turno][i][3],maior)
            solver.Add(solver.Sum(lista_capacidades[uc][turno]) <= int(maior * 1.12))
### TEORICAS ####
for uc in lista_capacidades:
    for turno in lista_capacidades[uc]:
        if uc[-2:] == suf_teoria:
            for i in range(len(slots[uc][turno])):
                maior = max(slots[uc][turno][i][3],maior)
            solver.Add(solver.Sum(lista_capacidades[uc][turno]) <= solver.infinity())

# Aulas sem sobreposicoes
# Percorre todos os alunos e todas as ucs e junta todos os seus turnos num dicionario do tipo de acordo com o seu dia e hora, do tipo {Aluno:{Dia:{Hora:[Ucs]}}}
# Por ultimo, a soma dessa lista com as Ucs num determinado dia, numa determinada hora tem de ser no maximo 1, ou seja, tem de haver no maximo uma alocaçao

turnos = {}
for al in presencas:
    if al not in turnos:
        turnos[al] = {}
    for uc in presencas[al]:
        for t in presencas[al][uc]:
            for d in dias_slots:
                if d not in turnos[al]:
                    turnos[al][d] = {}
                slot_max = dias_slots[d]
                for s in range(slot_max):
                    tuplo = slots[uc][t]
                    for i in range(len(tuplo)):
                        if tuplo[i][0] == d and (tuplo[i][1] <= s <= tuplo[i][2]):
                            if s not in turnos[al][d]:
                                turnos[al][d][s] = []
                            turnos[al][d][s] += [ presencas[al][uc][t] ]
# pprint.pprint(turnos)

for al in turnos:
    for d in turnos[al]:
        for s in turnos[al][d]:
            solver.Add(solver.Sum(turnos[al][d][s]) <= 1)

######### grupos #######
#Carrega os grupos e cria a restrição dos grupos 

grupos_c = []
for uc in grupos_json:
    for grupo in grupos_json[uc]:
        for t in slots[uc]:
            solver.Add(solver.Sum([ presencas[al][uc][t] for al in grupos_json[uc][grupo] ]) - (len(grupos_json[uc][grupo]) - 1) <= gruposCompletos[uc][grupo][t] )
            for al in grupos_json[uc][grupo]:
                solver.Add(presencas[al][uc][t] >= gruposCompletos[uc][grupo][t])

##################### OBJECTIVOS ######################################

#maximizar alocações nas teoricas
max_teoricas = solver.Sum([presencas[al][uc][turno] for al in presencas for uc in presencas[al] for turno in presencas[al][uc]])

# maximizar grupos juntos
max_grupos = solver.Sum([ gruposCompletos[uc][grupo][turno] for uc in gruposCompletos for grupo in gruposCompletos[uc] for turno in gruposCompletos[uc][grupo] ])

solver.Maximize(max_teoricas + max_grupos)

### Diminuir a diferença entre a uc com mais lotaçao e a que tem menos lotaçao
# dif_lot = 0
# for uc in lista_capacidades:
#     t = solver.Sum([solver.Sum(lista_capacidades[uc][turno]) for turno in lista_capacidades[uc]])
#     for turno in lista_capacidades[uc]:
#         dif_lot += t - solver.Sum(lista_capacidades[uc][turno])
# solver.Minimize(dif_lot)

solucao = solver.Solve()

if solucao != solver.OPTIMAL:
    print 'No solution found!'
    sys.exit()
else:
    print 'Found solution!'

print 'Total de alocações possiveis %s' % n_uc
print 'Total de alunos alocados %s' % solver.Objective().Value()
print 'Taxa de sucesso %.2f%%' % round(((solver.Objective().Value() * 100) / n_uc),2)
r = {}
for al in presencas:
    if al not in r:
        r[al] = {}
    for uc in presencas[al]:
        if uc not in r[al]:
            r[al][uc] = [] 
        for turno in presencas[al][uc]:
            aloc = presencas[al][uc][turno].solution_value()
            # aloc = collector.Value(best_solution, presencas[al][uc][turno])
            if aloc == 1:
                r[al][uc] += [turno]
# for grupo in dicionario_grupos:
#     print 'Grupo: %s %s' % (grupo[0],grupo[1]),
#     for al in dicionario_grupos[grupo]:
#         print '%s - %s |' % (al,al.solution_value()), 
#     print '\n'

print 'Time = %i ms' % solver.WallTime()
# pprint.pprint(r)
# #alunos alocados a todas as cadeiras que estao inscritos
total_aloc = 0
n_tur = 0
nao_alocados = []
nao_alocados_t = []
alocacoes_finais = {}

for al in r:  
    for u in r[al]:
        if u not in alocacoes_finais:
            alocacoes_finais[u] = {}
        for t in r[al][u]:
            n_tur += 1
            if t not in alocacoes_finais[u]:
                alocacoes_finais[u][t] = 1
            else:
                alocacoes_finais[u][t] += 1
    if n_tur >= len(r[al]) :
        total_aloc += 1
        n_tur = 0

# #calcular alunos alocados a todas as cadeiras que estao inscritos  
for al in alunos:
    for uc in alunos[al]:
        if not uc[-2:] == suf_teoria and len(r[al][uc]) == 0 and al not in nao_alocados:
            nao_alocados.append(al)
        if uc[-2:] == suf_teoria and len(r[al][uc]) == 0 and al not in nao_alocados_t:
            nao_alocados_t.append((al,uc))

# #calcular os grupos que ficaram juntos ou não
grupos_nao_juntos = []
for uc in grupos_json:
    for grupo in grupos_json[uc]:
        al1 = grupos_json[uc][grupo][0]
        turno = r[al1][uc][0]
        for al in grupos_json[uc][grupo]:
            if turno not in r[al][uc]:
                grupos_nao_juntos += [ uc+'_'+grupo+' : '+al ]

# ucs que ultrapassaram capacidade
ucs_maximo_capacidade = []
for uc in alocacoes_finais:
    for turno in alocacoes_finais[uc]:
        total = alocacoes_finais[uc][turno]
        for i in range(len(slots[uc][turno])):
            if total > slots[uc][turno][i][3]:
                ucs_maximo_capacidade += [(uc,turno,slots[uc][turno][i][3],total,total - slots[uc][turno][i][3])]

pprint.pprint(alocacoes_finais)
# pprint.pprint(r)
print 'Alunos alocados a todas as ucs: %s' % str(total_aloc)
print 'Alunos não alocados a praticas: '
pprint.pprint(nao_alocados)
print 'Alunos não alocados a teoricas: '
pprint.pprint(nao_alocados_t)
print 'grupos nao juntos: '
pprint.pprint(grupos_nao_juntos)
print 'Ucs com maior capacidade do que o suposto:'
pprint.pprint(ucs_maximo_capacidade)

def check_sobreposicoes(aluno):
    h = {}
    for uc in aluno:
        for turno in aluno[uc]:
            hI = hF = dia = 0
            for i in range(len(slots[uc][turno])):
                hI = slots[uc][turno][i][1]
                hF = slots[uc][turno][i][2]
                dia = slots[uc][turno][i][0]
                if dia not in h:
                    h[dia] = []
                if hI not in h[dia]:
                    h[dia].append((hI,hF-hI))
    # pprint.pprint(h)
    
    for dia in h:
        anterior = -1
        for (sI,sD) in sorted(h[dia], key=lambda tup: tup[0]):
            # print (sI,sD)
            if anterior >= sI:
                # print anterior
                print 'Dia %s, Slot %s,%s' % (dia,sI,sD)
                return False
            else:
                anterior = sI + sD
    return True

i = 0
for a in r:
    # print 'Aluno %s' % a
    if not check_sobreposicoes(r[a]):
        i += 1
        print '%s tem sobreposicoes' % a
print '%s tem sobreposicoes' % i

# escrever ficheiro enrollments
out_file = open('enrollments.json', 'w')
lista_enrollments = [] 
for al in r:
    for uc in r[al]:
        if uc[-2:] != suf_teoria and uc[:6] != 'ALMOCO':
            lista_enrollments.append({ 'student_id':al, 'course_id':uc, 'shift_id':r[al][uc][0] })


json.dump(lista_enrollments, out_file)
