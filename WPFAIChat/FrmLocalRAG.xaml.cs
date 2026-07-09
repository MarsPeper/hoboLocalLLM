using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Microsoft.Win32;

namespace WPFAIChat
{
    public partial class FrmLocalRAG : Window
    {
        private readonly HttpClient _httpClient;
        private readonly ObservableCollection<ChatMessageItem> _chatMessages;
        private readonly ObservableCollection<DocumentItem> _documents;
        private const string ApiBaseUrl = "http://127.0.0.1:8000/api/";
        private System.Windows.Threading.DispatcherTimer _statusTimer;

        public FrmLocalRAG()
        {
            InitializeComponent();
            _httpClient = new HttpClient { Timeout = TimeSpan.FromMinutes(10) };
            
            _chatMessages = new ObservableCollection<ChatMessageItem>();
            ChatItems.ItemsSource = _chatMessages;

            _documents = new ObservableCollection<DocumentItem>();
            LstDocuments.ItemsSource = _documents;

            // Add welcome message
            _chatMessages.Add(new ChatMessageItem
            {
                Avatar = "🤖",
                Role = "assistant",
                Content = "Hello! I am your local RAG desktop assistant. Ask me questions about the documents you index in the vector database.",
                BackgroundBrush = "#ffffff",
                BorderBrush = "#e0e0e0",
                SourcesVisibility = Visibility.Collapsed
            });

            Loaded += FrmLocalRAG_Loaded;
        }

        private async void FrmLocalRAG_Loaded(object sender, RoutedEventArgs e)
        {
            await UpdateApiStatusAsync();
            await LoadConfigAsync();
            await LoadDocumentsAsync();

            // Set up periodic API status checking (60 seconds for performance)
            _statusTimer = new System.Windows.Threading.DispatcherTimer();
            _statusTimer.Interval = TimeSpan.FromSeconds(60);
            _statusTimer.Tick += StatusTimer_Tick;
            _statusTimer.Start();
        }

        private async void StatusTimer_Tick(object sender, EventArgs e)
        {
            await UpdateApiStatusAsync();
        }

        private void MarkApiOnline()
        {
            ElpStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10b981"));
            TxtStatus.Text = "Local API Online (Port 8000)";
        }

        private void MarkApiOffline()
        {
            ElpStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#ef4444"));
            TxtStatus.Text = "Local API Offline (Port 8000)";
        }

        private async Task UpdateApiStatusAsync()
        {
            bool isOnline = false;
            try
            {
                // Ping the dedicated lightweight health endpoint
                var response = await _httpClient.GetAsync(ApiBaseUrl + "health");
                isOnline = response.IsSuccessStatusCode;
            }
            catch
            {
                isOnline = false;
            }

            if (isOnline)
            {
                MarkApiOnline();
            }
            else
            {
                MarkApiOffline();
            }
        }

        // Navigation Menu tab switching
        private void NavChanged(object sender, RoutedEventArgs e)
        {
            if (TxtHeaderTitle == null || GridChat == null || GridDocs == null || GridConfig == null) return;

            if (RadChat.IsChecked == true)
            {
                TxtHeaderTitle.Text = "Semantic Search & Chat";
                GridChat.Visibility = Visibility.Visible;
                GridDocs.Visibility = Visibility.Collapsed;
                GridConfig.Visibility = Visibility.Collapsed;
            }
            else if (RadDocs.IsChecked == true)
            {
                TxtHeaderTitle.Text = "Document Ingestion Registry";
                GridChat.Visibility = Visibility.Collapsed;
                GridDocs.Visibility = Visibility.Visible;
                GridConfig.Visibility = Visibility.Collapsed;
            }
            else if (RadConfig.IsChecked == true)
            {
                TxtHeaderTitle.Text = "System Parameters & Configurations";
                GridChat.Visibility = Visibility.Collapsed;
                GridDocs.Visibility = Visibility.Collapsed;
                GridConfig.Visibility = Visibility.Visible;
            }
        }

        #region CONFIGURATION TAB (Settings)

        private static string GetJsonString(JsonElement parent, string name, string defaultValue = "")
        {
            if (parent.TryGetProperty(name, out var prop))
            {
                if (prop.ValueKind == JsonValueKind.String)
                    return prop.GetString() ?? defaultValue;
                if (prop.ValueKind == JsonValueKind.Null)
                    return defaultValue;
                return prop.GetRawText();
            }
            return defaultValue;
        }

        private static int GetJsonInt(JsonElement parent, string name, int defaultValue = 0)
        {
            if (parent.TryGetProperty(name, out var prop))
            {
                if (prop.ValueKind == JsonValueKind.Number)
                    return prop.GetInt32();
                if (prop.ValueKind == JsonValueKind.String && int.TryParse(prop.GetString(), out var val))
                    return val;
            }
            return defaultValue;
        }

        private static double GetJsonDouble(JsonElement parent, string name, double defaultValue = 0.0)
        {
            if (parent.TryGetProperty(name, out var prop))
            {
                if (prop.ValueKind == JsonValueKind.Number)
                    return prop.GetDouble();
                if (prop.ValueKind == JsonValueKind.String && double.TryParse(prop.GetString(), out var val))
                    return val;
            }
            return defaultValue;
        }

        private static bool GetJsonBool(JsonElement parent, string name, bool defaultValue = false)
        {
            if (parent.TryGetProperty(name, out var prop))
            {
                if (prop.ValueKind == JsonValueKind.True) return true;
                if (prop.ValueKind == JsonValueKind.False) return false;
            }
            return defaultValue;
        }

        private async Task LoadConfigAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync(ApiBaseUrl + "config");
                if (response.IsSuccessStatusCode)
                {
                    MarkApiOnline();
                    var json = await response.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;

                    // Parse RAG
                    if (root.TryGetProperty("rag", out var rag))
                    {
                        TxtChunkSize.Text = GetJsonInt(rag, "chunk_size", 500).ToString();
                        TxtChunkOverlap.Text = GetJsonInt(rag, "chunk_overlap", 50).ToString();
                        ChkHybridSearch.IsChecked = GetJsonBool(rag, "use_hybrid_search", true);
                        
                        bool useReranker = GetJsonBool(rag, "use_reranker", true);
                        ChkReranker.IsChecked = useReranker;
                        TxtRerankerModel.Text = GetJsonString(rag, "reranker_model", "ms-marco-MiniLM-L-12-v2");
                        TxtTopK.Text = GetJsonInt(rag, "top_k", 4).ToString();
                        TxtBaseK.Text = GetJsonInt(rag, "base_retrieve_k", 12).ToString();

                        PanelRerank.Visibility = useReranker ? Visibility.Visible : Visibility.Collapsed;
                    }

                    // Parse LLM
                    if (root.TryGetProperty("llm", out var llm))
                    {
                        TxtLlmUrl.Text = GetJsonString(llm, "api_url", "http://localhost:8080/v1");
                        TxtLlmModel.Text = GetJsonString(llm, "model_name", "local-model");
                        TxtLlmTemp.Text = GetJsonDouble(llm, "temperature", 0.1).ToString("0.00");
                        TxtLlmMaxTokens.Text = GetJsonInt(llm, "max_tokens", 1024).ToString();
                        TxtSystemPrompt.Text = GetJsonString(llm, "system_prompt");
                    }

                    // Parse Embeddings & Qdrant
                    if (root.TryGetProperty("embedding", out var emb))
                    {
                        TxtEmbModel.Text = GetJsonString(emb, "model_name", "all-MiniLM-L6-v2");
                        TxtSparseModel.Text = GetJsonString(emb, "sparse_model_name", "Qdrant/bm25");
                        
                        string device = GetJsonString(emb, "device", "cpu");
                        foreach (ComboBoxItem item in CboEmbDevice.Items)
                        {
                            if (item.Content.ToString() == device)
                            {
                                CboEmbDevice.SelectedItem = item;
                                break;
                            }
                        }
                    }

                    if (root.TryGetProperty("qdrant", out var qdrant))
                    {
                        TxtQdrantCollection.Text = GetJsonString(qdrant, "collection_name", "local_rag_documents");
                        TxtQdrantPath.Text = GetJsonString(qdrant, "path");
                        TxtQdrantUrl.Text = GetJsonString(qdrant, "url", "http://localhost:6333");
                    }
                }
            }
            catch (Exception ex)
            {
                MarkApiOffline();
                MessageBox.Show($"Failed to load configuration: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ChkReranker_StateChanged(object sender, RoutedEventArgs e)
        {
            if (PanelRerank == null) return;
            PanelRerank.Visibility = ChkReranker.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
        }

        private async void BtnSaveConfig_Click(object sender, RoutedEventArgs e)
        {
            TxtConfigStatus.Text = "⚙️ Saving configuration...";
            TxtConfigStatus.Foreground = Brushes.DarkGoldenrod;

            try
            {
                // Construct the JSON structure matching ConfigUpdateRequest in backend
                var payloadObj = new Dictionary<string, object>
                {
                    { "rag", new Dictionary<string, object>
                        {
                            { "chunk_size", int.Parse(TxtChunkSize.Text) },
                            { "chunk_overlap", int.Parse(TxtChunkOverlap.Text) },
                            { "top_k", int.Parse(TxtTopK.Text) },
                            { "use_hybrid_search", ChkHybridSearch.IsChecked == true },
                            { "use_reranker", ChkReranker.IsChecked == true },
                            { "reranker_model", TxtRerankerModel.Text },
                            { "rerank_top_k", int.Parse(TxtTopK.Text) }, // backend requires both
                            { "base_retrieve_k", int.Parse(TxtBaseK.Text) }
                        }
                    },
                    { "embedding", new Dictionary<string, object>
                        {
                            { "model_name", TxtEmbModel.Text },
                            { "sparse_model_name", TxtSparseModel.Text },
                            { "device", ((ComboBoxItem)CboEmbDevice.SelectedItem).Content.ToString() }
                        }
                    },
                    { "qdrant", new Dictionary<string, object>
                        {
                            { "path", TxtQdrantPath.Text },
                            { "url", TxtQdrantUrl.Text },
                            { "collection_name", TxtQdrantCollection.Text }
                        }
                    },
                    { "llm", new Dictionary<string, object>
                        {
                            { "api_url", TxtLlmUrl.Text },
                            { "model_name", TxtLlmModel.Text },
                            { "temperature", double.Parse(TxtLlmTemp.Text) },
                            { "max_tokens", int.Parse(TxtLlmMaxTokens.Text) },
                            { "system_prompt", TxtSystemPrompt.Text }
                        }
                    }
                };

                string json = JsonSerializer.Serialize(payloadObj);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync(ApiBaseUrl + "config", content);

                if (response.IsSuccessStatusCode)
                {
                    MarkApiOnline();
                    TxtConfigStatus.Text = "✅ Configuration saved and hot-reloaded successfully!";
                    TxtConfigStatus.Foreground = Brushes.Green;
                }
                else
                {
                    string errorDetail = await response.Content.ReadAsStringAsync();
                    TxtConfigStatus.Text = $"❌ Failed to save: {errorDetail}";
                    TxtConfigStatus.Foreground = Brushes.Red;
                }
            }
            catch (Exception ex)
            {
                MarkApiOffline();
                TxtConfigStatus.Text = $"❌ Error: {ex.Message}";
                TxtConfigStatus.Foreground = Brushes.Red;
            }
        }

        #endregion

        #region DOCUMENT LIBRARY TAB

        private async Task LoadDocumentsAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync(ApiBaseUrl + "documents");
                if (response.IsSuccessStatusCode)
                {
                    MarkApiOnline();
                    var json = await response.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(json);
                    
                    _documents.Clear();
                    foreach (var element in doc.RootElement.EnumerateArray())
                    {
                        _documents.Add(new DocumentItem
                        {
                            FileName = element.GetProperty("file_name").GetString(),
                            ChunkCount = element.GetProperty("chunk_count").GetInt32()
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                MarkApiOffline();
                Console.WriteLine($"Error loading documents: {ex.Message}");
            }
        }

        private async void BtnUpload_Click(object sender, RoutedEventArgs e)
        {
            var openFileDialog = new OpenFileDialog
            {
                Filter = "Allowed Formats (*.txt;*.pdf;*.docx;*.doc)|*.txt;*.pdf;*.docx;*.doc|All Files (*.*)|*.*",
                Title = "Select File to Ingest"
            };

            if (openFileDialog.ShowDialog() == true)
            {
                string filePath = openFileDialog.FileName;
                string fileName = Path.GetFileName(filePath);
                
                try
                {
                    Cursor = Cursors.Wait;

                    using var form = new MultipartFormDataContent();
                    using var fileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
                    using var streamContent = new StreamContent(fileStream);
                    streamContent.Headers.ContentType = MediaTypeHeaderValue.Parse("application/octet-stream");
                    
                    form.Add(streamContent, "file", fileName);

                    var response = await _httpClient.PostAsync(ApiBaseUrl + "upload", form);
                    if (response.IsSuccessStatusCode)
                    {
                        MarkApiOnline();
                        Cursor = Cursors.Arrow;
                        await PollIngestionStatusAsync(fileName);
                    }
                    else
                    {
                        string errMsg = await response.Content.ReadAsStringAsync();
                        MessageBox.Show($"Upload failed to start: {errMsg}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
                catch (Exception ex)
                {
                    MarkApiOffline();
                    MessageBox.Show($"Upload error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                finally
                {
                    Cursor = Cursors.Arrow;
                }
            }
        }

        private async Task PollIngestionStatusAsync(string fileName)
        {
            PrgUpload.Visibility = Visibility.Visible;
            TxtUploadProgress.Visibility = Visibility.Visible;
            BtnUpload.IsEnabled = false;

            try
            {
                bool isDone = false;
                int retries = 0;
                while (!isDone)
                {
                    await Task.Delay(1000);

                    var response = await _httpClient.GetAsync(ApiBaseUrl + $"upload/status/{Uri.EscapeDataString(fileName)}");
                    if (!response.IsSuccessStatusCode)
                    {
                        retries++;
                        if (retries > 5)
                        {
                            throw new Exception("Status endpoint not responding or returning 404.");
                        }
                        continue;
                    }

                    MarkApiOnline();
                    retries = 0; // Reset retries on successful status fetch
                    var json = await response.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;
                    string status = root.GetProperty("status").GetString() ?? "extracting";

                    if (status == "extracting")
                    {
                        PrgUpload.IsIndeterminate = true;
                        TxtUploadProgress.Text = "📄 Extracting text and partition splitting...";
                    }
                    else if (status == "indexing")
                    {
                        int total = root.GetProperty("total_chunks").GetInt32();
                        int processed = root.GetProperty("processed_chunks").GetInt32();
                        
                        PrgUpload.IsIndeterminate = false;
                        PrgUpload.Maximum = total;
                        PrgUpload.Value = processed;
                        TxtUploadProgress.Text = $"⚡ Generating embeddings & indexing: {processed} / {total} chunks...";
                    }
                    else if (status == "completed")
                    {
                        isDone = true;
                        int total = root.GetProperty("total_chunks").GetInt32();
                        PrgUpload.IsIndeterminate = false;
                        PrgUpload.Value = total;
                        TxtUploadProgress.Text = "✅ Ingestion complete!";
                        MessageBox.Show($"File '{fileName}' successfully indexed into Qdrant vector store in {total} chunks!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
                        await LoadDocumentsAsync();
                    }
                    else if (status == "failed")
                    {
                        isDone = true;
                        string error = root.GetProperty("error").GetString() ?? "Unknown extraction error";
                        TxtUploadProgress.Text = "❌ Ingestion failed.";
                        MessageBox.Show($"Failed to ingest '{fileName}': {error}", "Ingestion Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
            }
            catch (Exception ex)
            {
                MarkApiOffline();
                MessageBox.Show($"Error while monitoring ingestion status: {ex.Message}", "Connection Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                PrgUpload.Visibility = Visibility.Collapsed;
                TxtUploadProgress.Visibility = Visibility.Collapsed;
                BtnUpload.IsEnabled = true;
            }
        }

        private async void BtnDeleteDoc_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string fileName)
            {
                var result = MessageBox.Show($"Are you sure you want to delete '{fileName}' from the vector database index?", "Confirm Deletion", MessageBoxButton.YesNo, MessageBoxImage.Warning);
                if (result == MessageBoxResult.Yes)
                {
                    try
                    {
                        Cursor = Cursors.Wait;
                        var response = await _httpClient.DeleteAsync(ApiBaseUrl + $"documents/{fileName}");
                        if (response.IsSuccessStatusCode)
                        {
                            MarkApiOnline();
                            await LoadDocumentsAsync();
                        }
                        else
                        {
                            string errMsg = await response.Content.ReadAsStringAsync();
                            MessageBox.Show($"Failed to delete document: {errMsg}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                    }
                    catch (Exception ex)
                    {
                        MarkApiOffline();
                        MessageBox.Show($"Deletion error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                    finally
                    {
                        Cursor = Cursors.Arrow;
                    }
                }
            }
        }

        #endregion

        #region CHAT INTERFACE & SSE STREAMING

        private async void BtnSend_Click(object sender, RoutedEventArgs e)
        {
            await SendQueryAsync();
        }

        private async void TxtInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                e.Handled = true;
                await SendQueryAsync();
            }
        }

        private async Task SendQueryAsync()
        {
            string question = TxtInput.Text.Trim();
            if (string.IsNullOrEmpty(question)) return;

            TxtInput.Clear();
            TxtInput.IsEnabled = false;
            BtnSend.IsEnabled = false;
            BdrLoader.Visibility = Visibility.Visible;

            // 1. Add User query message bubble
            _chatMessages.Add(new ChatMessageItem
            {
                Avatar = "👤",
                Role = "user",
                Content = question,
                BackgroundBrush = "#e2e2f6",
                BorderBrush = "#c8c6e5",
                SourcesVisibility = Visibility.Collapsed
            });

            // 2. Add Assistant empty stream placeholder bubble
            var assistantMsg = new ChatMessageItem
            {
                Avatar = "🤖",
                Role = "assistant",
                Content = "",
                BackgroundBrush = "#ffffff",
                BorderBrush = "#e0e0e0",
                SourcesVisibility = Visibility.Collapsed
            };
            _chatMessages.Add(assistantMsg);

            ChatScroller.ScrollToEnd();

            try
            {
                // Send query as JSON with stream = true
                var queryObj = new { question = question, stream = true };
                string jsonBody = JsonSerializer.Serialize(queryObj);
                var content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

                var request = new HttpRequestMessage(HttpMethod.Post, ApiBaseUrl + "query")
                {
                    Content = content
                };

                // Use ResponseHeadersRead to process the HTTP response streaming chunks
                var response = await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);
                
                if (!response.IsSuccessStatusCode)
                {
                    assistantMsg.Content = $"Error: API returned status {response.StatusCode}";
                    return;
                }

                MarkApiOnline();

                using var stream = await response.Content.ReadAsStreamAsync();
                using var reader = new StreamReader(stream);

                string line;
                while ((line = await reader.ReadLineAsync()) != null)
                {
                    if (string.IsNullOrEmpty(line)) continue;

                    if (line.StartsWith("data: "))
                    {
                        string dataVal = line.Substring(6).Trim();
                        if (dataVal == "[DONE]")
                        {
                            break;
                        }

                        try
                        {
                            using var parsedDoc = JsonDocument.Parse(dataVal);
                            var element = parsedDoc.RootElement;
                            string type = element.GetProperty("type").GetString();

                            if (type == "sources")
                            {
                                // Parse sources
                                var sourcesEl = element.GetProperty("sources");
                                var sourceList = new List<SourceItem>();

                                foreach (var src in sourcesEl.EnumerateArray())
                                {
                                    sourceList.Add(new SourceItem
                                    {
                                        FileName = src.GetProperty("file_name").GetString(),
                                        ChunkIndex = src.GetProperty("chunk_index").GetInt32(),
                                        Score = src.GetProperty("score").GetDouble(),
                                        Content = src.GetProperty("content").GetString()
                                    });
                                }

                                if (sourceList.Count > 0)
                                {
                                    // Update sources in UI thread
                                    Dispatcher.Invoke(() =>
                                    {
                                        assistantMsg.Sources = new ObservableCollection<SourceItem>(sourceList);
                                        assistantMsg.SourcesVisibility = Visibility.Visible;
                                    });
                                }
                            }
                            else if (type == "token")
                            {
                                string token = element.GetProperty("token").GetString();
                                
                                // Append character token in UI thread
                                Dispatcher.Invoke(() =>
                                {
                                    assistantMsg.Content += token;
                                });
                            }
                            else if (type == "error")
                            {
                                string errMsg = element.GetProperty("message").GetString();
                                Dispatcher.Invoke(() =>
                                {
                                    assistantMsg.Content = $"⚠️ Error: {errMsg}";
                                });
                            }
                        }
                        catch (Exception jsonEx)
                        {
                            Console.WriteLine($"JSON parse exception: {jsonEx.Message}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MarkApiOffline();
                assistantMsg.Content = $"⚠️ Connection Error: {ex.Message}";
            }
            finally
            {
                TxtInput.IsEnabled = true;
                BtnSend.IsEnabled = true;
                BdrLoader.Visibility = Visibility.Collapsed;
                TxtInput.Focus();
                ChatScroller.ScrollToEnd();
            }
        }

        #endregion
    }

    #region SUPPORT BINDING DATA MODELS

    public class ChatMessageItem : INotifyPropertyChanged
    {
        public string Avatar { get; set; }
        public string Role { get; set; }
        public string BackgroundBrush { get; set; }
        public string BorderBrush { get; set; }

        private string _content;
        public string Content
        {
            get => _content;
            set
            {
                _content = value;
                OnPropertyChanged(nameof(Content));
            }
        }

        private ObservableCollection<SourceItem> _sources = new ObservableCollection<SourceItem>();
        public ObservableCollection<SourceItem> Sources
        {
            get => _sources;
            set
            {
                _sources = value;
                OnPropertyChanged(nameof(Sources));
            }
        }

        private Visibility _sourcesVisibility = Visibility.Collapsed;
        public Visibility SourcesVisibility
        {
            get => _sourcesVisibility;
            set
            {
                _sourcesVisibility = value;
                OnPropertyChanged(nameof(SourcesVisibility));
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged(string name)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }
    }

    public class SourceItem
    {
        public string FileName { get; set; }
        public int ChunkIndex { get; set; }
        public double Score { get; set; }
        public string Content { get; set; }
        public string SummaryText => $"🔍 {FileName} (Chunk {ChunkIndex + 1} • Match: {Score * 100:F0}%)";
    }

    public class DocumentItem
    {
        public string FileName { get; set; }
        public int ChunkCount { get; set; }
    }

    #endregion
}
