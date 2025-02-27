import pandas as pd
import sys
import os, shutil
import re
import datetime

class Intelbras():

    def __init__(self, output_filename):        
        self.create_path()
        self.output_filename = f"{output_filename}_{datetime.date.today().strftime('%d-%m-%Y')}"

    def run(self, file):
        
        self.extract(file)
        self.transform()
        self.load()
        return os.path.join(self.output_dir, self.output_filename) + '.xlsx'

    def extract(self, excel_file):
        # lê a planilha e converte em um DataFrame
        self.df = pd.read_excel(excel_file)

        # filtra o DataFrame apenas com as colunas que importam
        self.df = self.df[
            [
                'nome',
                'numero_de_telefone', 
                'AUT.Fax', 
                'AUT.Telefone celular', 
                'AUT.Contato', 
                'AUT.Contato telefone'
            ]
        ]

        # converte o DataFrame em um dicionário com listas, sendo o nome da coluna a chave e o resto da coluna uma lista [] com os dados
        self.dicionario = self.df.to_dict('list')

    def transform(self):
        # define as colunas que vão ser alteradas
        colunas_com_telefones = [
            'numero_de_telefone', 
            'AUT.Fax', 
            'AUT.Telefone celular', 
            'AUT.Contato', 
            'AUT.Contato telefone'
        ]

        # itera entre as colunas
        for coluna in colunas_com_telefones:
            # contador para guiar a alteração dos dados, fazendo o papel de índice da lista. é zerado a cada nova coluna nesse processo.
            contador = 0

            # itera entre as células de cada coluna limpando os dados
            for item in self.dicionario[coluna]:
                try:
                    # converte o conteúdo da célula em string para evitar problemas com o tipo (algumas colunas vazias estavam sendo lidas como float, objeto não iterável, causando erro.)
                    item = str(item)
                    item = "".join([numero for numero in item if numero.isdigit()]) # mantém apenas os números em cada célula, tirando textos e caracteres desnecessários
                except Exception as e:
                    # em caso de erro, printa o erro, a célula que deu problema e encerra imediatamente a execução do programa
                    print(e)
                    print(item)
                    sys.exit(0)
                else:
                    # substitui o dado anterior pelo dado limpo e incrementa o contador para passar para a próxima célula
                    self.dicionario[coluna][contador] = item
                    contador += 1

        # transforma a tabela em DataFrame novamente e continua a limpeza
        self.df = pd.DataFrame(self.dicionario)

        # resume as colunas de telefone em apenas uma, repetindo o nome do cliente
        self.df = pd.melt(self.df, id_vars=['nome'], value_vars=colunas_com_telefones)
        self.df = self.df.sort_values(['nome'])
        self.df = self.df.drop('variable', axis=1)
        self.df = self.df[self.df['value'].str.match(r"^5?5?\d{0,2}9?\d{8}$")]
        self.df['value'] = self.df['value'].apply(self.clean_numbers)

        # identifica clientes com mais de um número cadastrado e sinaliza numa nova coluna
        self.df['duplicado'] = self.df['nome'].duplicated(keep=False)
        self.df['duplicado'] = self.df['duplicado'].replace(False, "")
        self.df['duplicado'] = self.df['duplicado'].replace(True, "DUPLICADO - VERIFICAR")

        # alterando formato para robô intelbras: "NOME DO CLIENTE,71912345678"
        self.df['data'] = self.df['nome'] + "," + self.df['value']
        self.df = self.df[["data", "duplicado"]]

        # última limpeza dos dados
        self.df = self.df.dropna() # remove valores nulos que podem surgir durante o tratamento
        self.df = self.df.drop_duplicates() # remove as linhas duplicadas (mesmo cliente e mesmo número de telefone)

    def load(self):
        # exporta os dados tratados em uma planilha Excel

        # verifica duplicidade de nome e incrementa para evitar substituição de arquivos
        counter = 1
        temp_output_filename = self.output_filename
        print(os.listdir(self.output_dir))
        while f'{temp_output_filename}.xlsx' in os.listdir(self.output_dir):
            counter += 1
            temp_output_filename = f'{self.output_filename}_{counter}'
        self.output_filename = f'{self.output_dir}/{temp_output_filename}'
        self.df.to_excel(f'{self.output_filename}.xlsx', index=False)

    def create_path(self):
        self.currentdir = os.getcwd()
        self.output_dir = os.path.join(self.currentdir, "planilhas_transformadas")


        if not os.path.exists(self.output_dir):
            print('Pasta de destino das planilhas não encontrada... Criando pra você')
            os.mkdir(self.output_dir)
        else:
            shutil.rmtree(self.output_dir)
            os.mkdir(self.output_dir)

    def clean_numbers(self, number):
        if number.startswith('55') and len(number) == 13:
            return number
        if len(number) == 9:
            return "5571" + number
        if len(number) == 10:
            return '55' + number[:2] + "9" + number[2:]
        if len(number) == 11:
            return '55' + number
    