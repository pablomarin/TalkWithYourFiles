import logging
from dotenv import load_dotenv
from file_handlers import FileHandlerFactory
from text_processor import DefaultTextProcessor
from qa_chain import QAChainRunner
from parameter_controller import ParameterController


"""
This file, flow_coordinator.py, serves as a central coordination module within the application. It acts as a bridge between user interface & underlying functionalities of other modules.
It is designed to make the application maintainable & flexible by not being dependent on a certain framework. As long as the logic & functionalities are provided here the run function will serve its purpose.

KEY FEATURES:
Loading Environment Variables: 
The load_dotenv() function is called to load the environment variables defined in the project's .env file. This ensures that sensitive or configurable information is securely accessed by the application.

File Handling: 
The FileHandlerFactory class from file_handlers.py is utilized to obtain the appropriate file handler based on the file type. The selected handler is then used to read the file's contents. 

Text Processing:
The DefaultTextProcessor class from text_processor.py provides text processing functionality, such as splitting text into chunks and creating embeddings.


Question-Answering Chain Execution: The QAChainRunner class from qa_chain.py is instantiated, representing the question-answering chain runner. This class uses an LLM to execute the chain. The get_relative_chunks() method finds the most relevant chunks in the knowledge base for a given user question, and the run_chain() method runs the question-answering chain on the provided documents and question.

Logging and Error Handling: The logging module is used to provide informative log messages at various stages of the process. These messages indicate warnings or errors encountered during file processing, text extraction, chunk splitting, embedding creation, and question-answering chain execution. Appropriate error messages are returned if any critical issues arise, ensuring proper feedback to the user.

run() Function: The main function in this file is the run() function, which takes the uploaded files and user's question as input. It performs the necessary steps of file processing, text extraction, chunk splitting, embedding creation, and question-answering chain execution. If any issues occur during the process, it returns informative error messages. Otherwise, it returns the response generated by the question-answering chain.

"""
class FlowCoordinator:
    def __init__(self, param_controller):
        """Constructor for FlowCoordinator"""
        self.param_controller = param_controller
        
        load_dotenv()
        logging.basicConfig(level=logging.INFO)


        self.factory = FileHandlerFactory()
        self.processor = DefaultTextProcessor(param_controller)
        self.runner = QAChainRunner(param_controller)
        self.runner.setup()

    ### add in more comments - step by step explanations
    def run(self, files, user_question):
        """Main function to process uploaded files and user's question, and run QA chain runner.
        Args:
            files: List of uploaded files.
            user_question: User's question input.
        Returns:
            str: The response from the QA chain runner.
        """

        if files and len(files) > 3:
            logging.warning("Please upload a maximum of 3 files")
            return "Please upload a maximum of 3 files"

        if user_question and files:
            combined_text = ""
            for file in files:
                if file is not None:
                    handler = self.factory.get_file_handler(file.type)
                    text = handler.read_file(file)
                    if not text:
                        logging.error(f"No text could be extracted from {file.name}. Please ensure the file is not encrypted or corrupted.")
                        return f"No text could be extracted from {file.name}. Please ensure the file is not encrypted or corrupted."
                    else:
                        combined_text += text

            if not combined_text:
                logging.warning("No text could be extracted from the provided files. Please try again with different files.")
                return "No text could be extracted from the provided files. Please try again with different files."

            chunks = self.processor.split_text(combined_text)
            if not chunks:
                logging.warning("Couldn't split the text into chunks. Please try again with different text.")
                return "Couldn't split the text into chunks. Please try again with different text."

            knowledge_base = self.processor.create_embeddings(chunks)
            if not knowledge_base:
                logging.warning("Couldn't create embeddings from the text. Please try again.")
                return "Couldn't create embeddings from the text. Please try again."

            docs = self.runner.get_relative_chunks(knowledge_base, user_question)
            if not docs:
                logging.warning("Couldn't find any relevant chunks for your question. Please try asking a different question.")
                return "Couldn't find any relevant chunks for your question. Please try asking a different question."

            return self.runner.run_chain(docs, user_question)
