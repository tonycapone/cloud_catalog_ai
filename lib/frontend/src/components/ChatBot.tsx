import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  List, 
  ListItem, 
  Link,
  Container,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Chip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  text: string;
  isUser: boolean;
  sources?: string[];
}

interface ChatBotProps {
  backendUrl: string;
}

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const ChatBot: React.FC<ChatBotProps> = ({ backendUrl }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [promptModifier, setPromptModifier] = useState('Informative, empathetic, and friendly');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    fetchSuggestedQuestions();
  }, [backendUrl]);

  const fetchSuggestedQuestions = async () => {
    try {
      const response = await fetch(`${backendUrl}/chat-suggested-questions`);
      const data = await response.json();
      
      setSuggestedQuestions(data);
    } catch (error) {
      console.error('Error fetching suggested questions:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent, questionOverride?: string) => {
    e.preventDefault();
    const questionToSend = questionOverride || input;
    if (!questionToSend.trim() || isLoading) return;

    const userMessage: Message = { text: questionToSend, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: questionToSend,
          chat_history: messages.map(m => m.text),
          prompt_modifier: promptModifier
        }),
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let botMessage: Message = { text: '', isUser: false };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'metadata') {
                botMessage.sources = data.sources;
                setMessages(prev => [...prev, { ...botMessage }]);
              } else if (data.type === 'content') {
                botMessage.text += data.content;
                setMessages(prev => [...prev.slice(0, -1), { ...botMessage }]);
              } else if (data.type === 'stop') {
                console.log('Response complete');
              }
            } catch (error) {
              console.error('Error parsing SSE data:', error);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error fetching response:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    handleSubmit({ preventDefault: () => {} } as React.FormEvent, question);
  };

  const renderMessageText = (text: string) => {
    return text.split('<br>').map((paragraph, index) => (
      <Typography key={index} variant="body1" paragraph>
        {paragraph}
      </Typography>
    ));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="md">
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', py: 2 }}>
          <Paper elevation={3} sx={{ flexGrow: 1, mb: 2, overflow: 'auto', p: 2, display: 'flex', flexDirection: 'column' }}>
            <List sx={{ flexGrow: 1 }}>
              {messages.map((message, index) => (
                <ListItem key={index} sx={{ flexDirection: 'column', alignItems: message.isUser ? 'flex-end' : 'flex-start' }}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 2, 
                      maxWidth: '70%', 
                      bgcolor: message.isUser ? '#e6f2ff' : '#fff0f5', // Softer pastel colors
                      color: message.isUser ? '#333' : '#333', // Darker text for better readability
                      borderRadius: '12px', // Rounded corners
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)', // Subtle shadow
                    }}
                  >
                    {renderMessageText(message.text)}
                  </Paper>
                  {message.sources && (
                    <Box sx={{ mt: 1, alignSelf: 'flex-start' }}>
                      <Typography variant="caption" sx={{ color: '#666' }}>Helpful links:</Typography>
                      <List dense>
                        {message.sources.map((source, idx) => (
                          <ListItem key={idx} disablePadding>
                            <Link href={source} target="_blank" rel="noopener noreferrer" sx={{ color: '#1976d2' }}>
                              <Typography variant="caption">{source}</Typography>
                            </Link>
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </ListItem>
              ))}
            </List>
            <div ref={messagesEndRef} />
            {suggestedQuestions.length > 0 && (
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {suggestedQuestions.map((question, index) => (
                  <Chip
                    key={index}
                    label={question}
                    onClick={() => handleSuggestedQuestionClick(question)}
                    color="primary"
                    variant="outlined"
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            )}
          </Paper>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question!"
              disabled={isLoading}
            />
            <Button type="submit" variant="contained" endIcon={<SendIcon />} disabled={isLoading}>
              Send
            </Button>
          </Box>
          <TextField
            fullWidth
            multiline
            rows={2}
            margin="normal"
            label="Prompt Modifier"
            variant="outlined"
            value={promptModifier}
            onChange={(e) => setPromptModifier(e.target.value)}
          />
        </Box>
      </Container>
    </ThemeProvider>
  );
};

export default ChatBot;