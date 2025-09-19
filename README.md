# mcp-chatbot

A network communications project (Proyect 1 — Networks) implementing a chatbot using an existing protocol.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture & Design](#architecture--design)
4. [Setup & Usage](#setup--usage)
5. [Examples](#examples)
6. [Dependencies](#dependencies)

---

## Overview

The **mcp-chatbot** project is part of a networks course requirement. The goal is to build a chatbot that communicates following a predefined or existing protocol. It emphasizes:

* Handling network communication correctly
* Parsing / formatting messages according to protocol rules
* Maintaining a responsive chatbot behavior

---

## Features

* Supports sending and receiving messages over the network according to protocol specifications
* Ability to parse incoming requests and to send valid responses
* Error handling for protocol violations or malformed messages
* Local server support for testing

---

## Architecture & Design

* **Protocol Layer**: Ensures messages follow the required protocol (format, fields, sequencing, etc.)
* **Communication Layer**: Manages connections, sending and receiving over sockets (or equivalent)
* **Chatbot Logic**: Interprets messages and determines appropriate responses
* **Server / Client Mode**: A server that listens for connections; client(s) that connect and send requests

---

## Setup & Usage

Here’s how to get the project running:

1. Clone the repository:

   ```bash
   git clone https://github.com/Fabiola-cc/mcp-chatbot.git
   cd mcp-chatbot
   ```

2. Make sure you have the required dependencies installed (see [Dependencies](#dependencies)).

3. Run the server locally (if applicable). Example:

   ```bash
   python server.py
   ```

4. Connect a client or send messages following the protocol. Example:

   ```bash
   python client.py
   ```

5. Test sending and receiving messages; see how the chatbot responds.

---

## Examples

Here are some example interactions:

* Client: `HELLO protocol_message`
  Server/Chatbot: `WELCOME your_name`

* Client sends malformed message → Chatbot replies with error code or message

* Multiple clients connect and interact with server

*(These are illustrative—actual message formats depend on your protocol specification.)*

---

## Dependencies

* Python 3.x
* Any libraries used for networking (e.g. `socket`)
* Possibly others depending on protocol implementation (parsing, threading, etc.)