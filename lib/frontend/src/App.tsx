import React, { useState, useMemo } from 'react';
import { CssBaseline, Tabs, Tab, Box } from '@mui/material';
import ChatBot from './components/ChatBot';
import ProductGrid from './components/Products';

function App() {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  // Memoize the ProductGrid component
  const memoizedProductGrid = useMemo(() => <ProductGrid />, []);

  return (
    <>
      <CssBaseline />
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange}>
          <Tab label="Chat" />
          <Tab label="Products" />
        </Tabs>
      </Box>
      <Box sx={{ p: 3 }}>
        {value === 0 && <ChatBot />}
        {value === 1 && memoizedProductGrid}
      </Box>
    </>
  );
}

export default App;