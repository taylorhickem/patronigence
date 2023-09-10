import os
import pandas as pd
import matplotlib.pyplot as plt
from transformers import GPT2TokenizerFast
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
import textract


EXCEPTIONS = {
    'read_pdf': 'ERROR. problem encountered when attempting to read pdf document. '
}
FILES = {
    'openai_key': 'OPENAI_API_KEY',
    'FAISS_index': 'FAISS_index'
}
SETTINGS_DEFAULT = {
    'tokenizer': {
        'CHUNK_SIZE': 512,
        'CHUNK_OVERLAP': 24,
        'SEPARATORS': ["\n\n\n\n\n\n", "\n\n\n\n\n", "\n\n\n\n", "\n\n\n", "\n\n", "\n", " ", ""]
    },
    'chain': {
        'model': 'OpenAI',
        'temperature': 0,
        'chain_type': 'stuff'
    }
}
ENCODING_PDF = 'ISO-8859-1'
ENCODING_TEXT = 'utf-8'
TEXT_LEN_LIMIT = 16000


def load():
    load_openai_key()


def load_openai_key(key='', filepath=''):
    if not key:
        if not filepath:
            filepath = FILES['openai_key']
        with open(filepath, 'r') as f:
            key = f.read()
            f.close()
    os.environ['OPENAI_API_KEY'] = key


class Wilson(object):
    DOC_DIR = ''
    chunks = []
    exceptions_printout = False
    settings = SETTINGS_DEFAULT.copy()
    vector_db = None
    chain = None

    def __init__(self, document_dir=''):
        if document_dir:
            self.DOC_DIR = document_dir
        load()

    def vector_db_load(self, file_path='', dir_path='', suppress=False, settings={},
                           create_from_pdfs=False, append=False, embedding='OpenAI'):
        if create_from_pdfs:
            self.vector_db_create(dir_path=dir_path, suppress=suppress, settings=settings,
                                      load_pdfs=True, append=append, embedding=embedding)
        else: # load from file
            if not file_path:
                file_path = FILES['FAISS_index']
            if embedding == 'OpenAI':
                embeddings = Wilson.get_embeddings(embedding)
                self.vector_db = FAISS.load_local(file_path, embeddings)

    def _vector_db_save(self, file_path=''):
        if not file_path:
            file_path = FILES['FAISS_index']
        self.vector_db.save_local(file_path)

    def vector_db_create(self, dir_path='', suppress=False, settings={},
                         load_pdfs=True, append=False, embedding='OpenAI'):
        if load_pdfs:
            self.pdfs_load(dir_path=dir_path, suppress=suppress, settings=settings, append=append)

        if self.chunks:
            embeddings = None
            if embedding == 'OpenAI':
                embeddings = Wilson.get_embeddings(embedding)
            if embeddings is not None:
                self.vector_db = FAISS.from_documents(self.chunks, embeddings)
                self._vector_db_save()

    def pdfs_load(self, dir_path='', suppress=False, settings={}, append=False):
        if not append:
            self.chunks = []
        if not settings:
            settings = self.settings['tokenizer'].copy()

        if not dir_path:
            dir_path = self.DOC_DIR
        pdfs = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f[-4:] == '.pdf']
        try:
            self.chunks = Wilson.chunks_from_pdfs(pdfs, settings=settings)
        except Exception as e:
            self._exception_handle(
                exception_type='read_pdf', exception=e, suppress=suppress)

    def chain_load(self, **kwargs):
        settings = self.settings['chain'].copy()
        for k in settings.keys():
            if k in kwargs:
                settings[k] = kwargs[k]

        if settings['model'] == 'OpenAI':
            model = OpenAI(temperature=settings['temperature'])
            self.chain = load_qa_chain(
                model,
                chain_type=settings['chain_type'])

    def doc_query(self, query):
        docs = []
        if self.vector_db is not None:
            docs = self.vector_db.similarity_search(query)
        return docs

    def chain_prompt(self, prompt):
        response = 'chain not loaded.'
        if self.chain is not None:
            docs = self.doc_query(prompt)
            if len(docs) > 0:
                response = self.chain.run(input_documents=docs, question=prompt)
            else:
                response = 'vector query returned 0 docs. check if vector db is loaded.'
        return response

    @staticmethod
    def get_embeddings(embedding='OpenAI'):
        embeddings = None
        if embedding == 'OpenAI':
            embeddings = OpenAIEmbeddings()
        return embeddings

    @staticmethod
    def text_from_pdf(filepath):
        pdf = textract.process(filepath, input_encoding=ENCODING_PDF)

        # Save to .txt and reopen
        textpath = filepath[:-4] + '.txt'
        with open(textpath, 'w', encoding=ENCODING_TEXT) as f:
            f.write(pdf.decode(ENCODING_TEXT))
            f.close()
        with open(textpath, 'r', encoding=ENCODING_TEXT) as f:
            text = f.read()
            f.close()

        return text

    @staticmethod
    def chunks_from_pdfs(file_paths, settings={}):
        chunks = []
        texts = []
        if not settings:
            settings = SETTINGS_DEFAULT['tokenizer'].copy()

        for f in file_paths:
            text = Wilson.text_from_pdf(f)
            texts.append(text[:TEXT_LEN_LIMIT])

        def length_function(txt: str) -> int:
            tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')
            length = len(tokenizer.encode(txt))
            return length

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings['CHUNK_SIZE'],
            chunk_overlap=settings['CHUNK_OVERLAP'],
            separators=settings['SEPARATORS'],
            length_function=length_function
        )
        chunks = text_splitter.create_documents(texts)
        return chunks


    def _exception_handle(self, exception_type='', message='',
                          exception=None, suppress=False):
        exception_message = message
        if exception_type in EXCEPTIONS:
            exception_message = EXCEPTIONS[exception_type] + message
        if exception:
            exception_message = exception_message + str(exception)

        self.errors = exception_message
        if self.exceptions_printout:
            print(exception_message)

        if exception and (not suppress):
            raise ValueError(exception_message) from exception
