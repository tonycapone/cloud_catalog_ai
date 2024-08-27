import React, { useState, useEffect } from 'react';
import { Typography, Paper, CircularProgress, Box, Button } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

interface ProductInfo {
  summary: string;
  sources?: string[];
}

const ProductDetails: React.FC = () => {
  const { productName } = useParams<{ productName: string }>();
  const navigate = useNavigate();
  const [productInfo, setProductInfo] = useState<ProductInfo>({ summary: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProductDetails = async () => {
      try {
        const response = await fetch(`http://localhost:5000/product-details/${encodeURIComponent(productName || '')}`);
        if (!response.ok) {
          throw new Error('Failed to fetch product details');
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let currentSummary = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                switch (data.type) {
                  case 'initial':
                    currentSummary = '';
                    break;
                  case 'content':
                    currentSummary += data.content;
                    setProductInfo(prev => ({ ...prev, summary: currentSummary }));
                    break;
                  case 'metadata':
                    setProductInfo(prev => ({ ...prev, sources: data.sources }));
                    break;
                  case 'stop':
                    setLoading(false);
                    break;
                }
              } catch (error) {
                console.error('Error parsing SSE data:', error);
              }
            }
          }
        }
      } catch (error) {
        console.error('Error fetching product details:', error);
        setError(error instanceof Error ? error.message : 'An error occurred');
        setLoading(false);
      }
    };

    fetchProductDetails();
  }, [productName]);

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 800, margin: 'auto', mt: 4 }}>
      <Button onClick={() => navigate(-1)} sx={{ mb: 2 }}>Back to Products</Button>
      <Typography variant="h4" gutterBottom>{productName}</Typography>
      {loading && <CircularProgress />}
      <ReactMarkdown>{productInfo.summary}</ReactMarkdown>
      {productInfo.sources && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Sources:</Typography>
          <ul>
            {productInfo.sources.map((source, index) => (
              <li key={index}>
                <a href={source} target="_blank" rel="noopener noreferrer">{source}</a>
              </li>
            ))}
          </ul>
        </Box>
      )}
    </Paper>
  );
};

export default ProductDetails;