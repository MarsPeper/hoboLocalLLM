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
        private const string ApiBaseUrl = "http://localhost:8000/api/";

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
                BackgroundBrush = "#1e293b",
                BorderBrush = "#334155",
                SourcesVisibility = Visibility.Collapsed
            });

            Loaded += FrmLocalRAG_Loaded;
        }

        private async void FrmLocalRAG_Loaded(object sender, RoutedEventArgs e)
        {
            await LoadConfigAsync();
            await LoadDocumentsAsync();
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

        private async Task LoadConfigAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync(ApiBaseUrl + "config");
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;

                    // Parse RAG
                    var rag = root.GetProperty("rag");
                    TxtChunkSize.Text = rag.GetProperty("chunk_size").GetInt32().ToString();
                    TxtChunkOverlap.Text = rag.GetProperty("chunk_overlap").GetInt32().ToString();
                    ChkHybridSearch.IsChecked = rag.GetProperty("use_hybrid_search").GetBoolean();
                    
                    bool useReranker = rag.GetProperty("use_reranker").GetBoolean();
                    ChkReranker.IsChecked = useReranker;
                    TxtRerankerModel.Text = rag.GetProperty("reranker_model").GetString();
                    TxtTopK.Text = rag.GetProperty("top_k").GetInt32().ToString();
                    TxtBaseK.Text = rag.GetProperty("base_retrieve_k").GetInt32().ToString();

                    PanelRerank.Visibility = useReranker ? Visibility.Visible : Visibility.Collapsed;

                    // Parse LLM
                    var llm = root.GetProperty("llm");
                    TxtLlmUrl.Text = llm.GetProperty("api_url").GetString();
                    TxtLlmModel.Text = llm.GetProperty("model_name").GetString();
                    TxtLlmTemp.Text = llm.GetProperty("temperature").GetDouble().ToString("0.00");
                    TxtLlmMaxTokens.Text = llm.GetProperty("max_tokens").GetInt32().ToString();
                    TxtSystemPrompt.Text = llm.GetProperty("system_prompt").GetString();

                    // Parse Embeddings & Qdrant
                    var emb = root.GetProperty("embedding");
                    TxtEmbModel.Text = emb.GetProperty("model_name").GetString();
                    TxtSparseModel.Text = emb.GetProperty("sparse_model_name").GetString();
                    
                    string device = emb.GetProperty("device").GetString() ?? "cpu";
                    foreach (ComboBoxItem item in CboEmbDevice.Items)
                    {
                        if (item.Content.ToString() == device)
                        {
                            CboEmbDevice.SelectedItem = item;
                            break;
                        }
                    }

                    var qdrant = root.GetProperty("qdrant");
                    TxtQdrantCollection.Text = qdrant.GetProperty("collection_name").GetString();
                    TxtQdrantPath.Text = qdrant.GetProperty("path").GetString();
                    TxtQdrantUrl.Text = qdrant.GetProperty("url").GetString();
                }
            }
            catch (Exception ex)
            {
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
            TxtConfigStatus.Foreground = Brushes.Yellow;

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
                    TxtConfigStatus.Text = "✅ Configuration saved and hot-reloaded successfully!";
                    TxtConfigStatus.Foreground = Brushes.LightGreen;
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
                BackgroundBrush = "Transparent",
                BorderBrush = "#1f2937",
                SourcesVisibility = Visibility.Collapsed
            });

            // 2. Add Assistant empty stream placeholder bubble
            var assistantMsg = new ChatMessageItem
            {
                Avatar = "🤖",
                Role = "assistant",
                Content = "",
                BackgroundBrush = "#1e293b",
                BorderBrush = "#334155",
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
