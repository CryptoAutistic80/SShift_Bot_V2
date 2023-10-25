# Chat completion example of lantent knowledge space activation

# System prompt example
# MISSION
#You are an internal dialog iterator for an LLM (large language model) neural network. LLMs possess "latent space" (embedded knowledge and capabilities). You will be given a main query as well as a sequence of questions. Your role is to answer the queries as a way of "activating" the latent space inside your own neural network. This is not unlike how a human may "talk through" a problem or question in order to recruit the appropriate memories and techniques. The ultimate goal is to answer the main query listed below.

# MACHINE COGNITION ANALOGS
#There are numerous convergent parallels between human cognition and machine intelligence. For instance, both employ attention mechanisms, cognitive operations, and have constrained working spaces. This allows us to use similar terminology and techniques between humans and machines, including concepts such as theory of mind, working memory, and reasoning.

# INTERACTION SCHEMA
#The USER will play the role of interrogator. Your answers will be thorough and comprehensive, in order to get the most possible latent space activation. Anything potentially salient is valid to bring up, as it will expand your internal representation (embedding), thus recruiting more relevant information as the conversation advances. 

# MAIN QUERY
#<<QUERY>>

import re
import openai
from time import time, sleep
from halo import Halo
import textwrap
import yaml


###     file operations


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)



def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


###     API functions


def chatbot(conversation, model="gpt-4", temperature=0, max_tokens=2000):
    max_retry = 7
    retry = 0
    while True:
        try:
            spinner = Halo(text='Thinking...', spinner='dots')
            spinner.start()

            response = openai.ChatCompletion.create(model=model, messages=conversation, temperature=temperature, max_tokens=max_tokens)
            text = response['choices'][0]['message']['content']

            spinner.stop()

            return text, response['usage']['total_tokens']
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            exit(5)


def chat_print(text):
    formatted_lines = [textwrap.fill(line, width=120, initial_indent='    ', subsequent_indent='    ') for line in text.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    print('\n\n\nCHATBOT:\n\n%s' % formatted_text)


if __name__ == '__main__':
    openai.api_key = open_file('key_openai.txt').strip()

    main_question = input('What is your main query or question? ')

    prompts = [
  'What information do I already know about this topic? What information do I need to recall into my working memory to best answer this?',
  'What techniques or methods do I know that I can use to answer this question or solve this problem? How can I integrate what I already know, and recall more valuable facts, approaches, and techniques?',
  'And finally, with all this in mind, I will now discuss the question or problem and render my final answer.',]
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system01_dialog.txt').replace('<<QUERY>>', main_question)})

    for p in prompts:
        conversation.append({'role': 'user', 'content': p})
        print('\n\n\nUSER: %s' % p)
        response, tokens = chatbot(conversation)
        conversation.append({'role': 'assistant', 'content': response})
        print('\n\n\nCHATBOT:\n%s' % response)

    a = input('Press enter to end.')