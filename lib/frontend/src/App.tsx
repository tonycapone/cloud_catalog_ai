import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import ProductGrid from './components/Products';
import ProductDetails from './components/ProductDetails';
import ChatBot from './components/ChatBot';
import { Box, Container, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const App: React.FC = () => {
  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              RGA Assistant
            </Typography>
            <Button color="inherit" component={RouterLink} to="/products">
              Products
            </Button>
            <Button color="inherit" component={RouterLink} to="/">
              Chat
            </Button>
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Routes>
            <Route path="/" element={<ChatBot />} />
            <Route path="/products" element={<ProductGrid />} />
            <Route path="/product/:productName" element={<ProductDetails />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
};

export default App;