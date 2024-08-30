import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import ProductGrid from './components/Products';
import ProductDetails from './components/ProductDetails';
import ChatBot from './components/ChatBot';
import { Box, Container, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

// Custom hook to fetch config
const useConfig = () => {
  const [config, setConfig] = useState<{ 
    backendUrl: string,
    customerName: string
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch('/config.json')
      .then(response => response.json())
      .then(data => {
        setConfig(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { config, loading, error };
};

const App: React.FC = () => {
  const { config, loading, error } = useConfig();
  document.title = `${config?.customerName} AI Assistant`;
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error loading config: {error.message}</div>;
  if (!config) return <div>Config not available</div>;

  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography
              variant="h6"
              component={RouterLink}
              to="/"
              sx={{
                textDecoration: 'none',
                color: 'inherit',
                '&:hover': {
                  cursor: 'pointer',
                },
                marginRight: 2,
              }}
            >
              {config.customerName} Assistant
            </Typography>
            <Button color="inherit" component={RouterLink} to="/">
              Chat
            </Button>
            <Button color="inherit" component={RouterLink} to="/products" sx={{ marginRight: 1 }}>
              Products
            </Button>

            <Box sx={{ flexGrow: 1 }} />
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Routes>
            <Route path="/" element={<ChatBot backendUrl={config.backendUrl} customerName={config.customerName} />} />
            <Route path="/products" element={<ProductGrid backendUrl={config.backendUrl} />} />
            <Route path="/product/:productName" element={<ProductDetails backendUrl={config.backendUrl} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
};

export default App;