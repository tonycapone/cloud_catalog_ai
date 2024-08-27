import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  List, 
  ListItem, 
  ListItemText,
  Link,
  Container,
  ThemeProvider,
  createTheme,
  CssBaseline
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  text: string;
  isUser: boolean;
  sources?: string[];
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

const ChatBot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [promptModifier, setPromptModifier] = useState('Informative, empathetic, and friendly');
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { text: input, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await axios.post('http://localhost:5000/chat', {
        question: input,
        chat_history: messages.map(m => [m.text, '']),
        prompt_modifier: promptModifier
      });

      const botMessage: Message = {
        text: response.data.answer,
        isUser: false,
        sources: response.data.sources
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error fetching response:', error);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="md">
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', py: 2 }}>
          <Paper elevation={3} sx={{ flexGrow: 1, mb: 2, overflow: 'auto', p: 2 }}>
            <List>
              {messages.map((message, index) => (
                <ListItem key={index} sx={{ flexDirection: 'column', alignItems: message.isUser ? 'flex-end' : 'flex-start' }}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 2, 
                      maxWidth: '70%', 
                      bgcolor: message.isUser ? 'primary.light' : 'secondary.light',
                      color: message.isUser ? 'primary.contrastText' : 'secondary.contrastText'
                    }}
                  >
                    <Typography variant="body1">{message.text}</Typography>
                  </Paper>
                  {message.sources && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption">Helpful links:</Typography>
                      <List dense>
                        {message.sources.map((source, idx) => (
                          <ListItem key={idx} disablePadding>
                            <Link href={source} target="_blank" rel="noopener noreferrer">
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
          </Paper>
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question!"
            />
            <Button type="submit" variant="contained" endIcon={<SendIcon />}>
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