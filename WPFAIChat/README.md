# WPFAIChat: Windows Native Desktop Client for hoboLocalLLM

**WPFAIChat** is a native Windows desktop client built with C# and WPF (.NET 9) that connects directly to the local **FastAPI Backend Server** (running on port `8000`). It provides a fast, responsive user interface to manage documents, customize configuration parameters, and chat with your local documents.

---

## 🚀 Features

- **Sleek Windows UI**: Built with a clean dark-themed layout featuring responsive navigation tabs.
- **Semantic Search Chat**: Streams token-by-token responses from the local LLM using Server-Sent Events (SSE).
- **Source Citations**: Displays document citations and matching scores directly in the chat bubbles.
- **Document Management**: View currently indexed files in the Qdrant database, delete documents, and upload new ones (PDF, DOCX, TXT, MD).
- **System Config Editor**: Tweak chunk sizes, overlap parameters, hybrid search toggles, reranker settings, and system prompt templates directly from the client.

---

## 📁 Project Structure

- **[App.xaml](file:///c:/Projects/hoboLocalLLM/WPFAIChat/App.xaml)**: Application entry definition.
- **[FrmLocalRAG.xaml](file:///c:/Projects/hoboLocalLLM/WPFAIChat/FrmLocalRAG.xaml)**: XAML layout file defining the interface panels (Chat, Document Library, Settings Panel).
- **[FrmLocalRAG.xaml.cs](file:///c:/Projects/hoboLocalLLM/WPFAIChat/FrmLocalRAG.xaml.cs)**: Code-behind managing API interactions, UI states, document upload threads, and response streaming.
- **[WPFAIChat.csproj](file:///c:/Projects/hoboLocalLLM/WPFAIChat/WPFAIChat.csproj)**: .NET project file declaring dependencies and target frameworks.

---

## 🛠️ Prerequisites

- **Operating System**: Windows 10 or Windows 11.
- **SDK**: [.NET 9.0 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/9.0) or higher.
- **Backend Services**: The FastAPI backend server and Qdrant DB must be running (`.\start_rag.ps1` in the `LocalRAG` directory).

---

## 🏃 Running the Client

### Option 1: Command Line (dotnet CLI)

1. Open PowerShell or Command Prompt.
2. Navigate to the `WPFAIChat` directory:
   ```powershell
   cd C:\Projects\hoboLocalLLM\WPFAIChat
   ```
3. Run the application:
   ```powershell
   dotnet run
   ```

### Option 2: Visual Studio

1. Open the solution folder in Visual Studio 2022 or VS Code.
2. Open [WPFAIChat.csproj](file:///c:/Projects/hoboLocalLLM/WPFAIChat/WPFAIChat.csproj) (or the solution file).
3. Press `F5` to build and run the project.

---

## ⚙️ Configuration

By default, the client points to `http://localhost:8000/api/` (the standard FastAPI endpoint). If your backend is hosted on a different machine or port, you can update the `ApiBaseUrl` constant in [FrmLocalRAG.xaml.cs](file:///c:/Projects/hoboLocalLLM/WPFAIChat/FrmLocalRAG.xaml.cs#L24):

```csharp
private const string ApiBaseUrl = "http://localhost:8000/api/";
```
