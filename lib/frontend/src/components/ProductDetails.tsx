import React, { useState, useEffect, useRef } from 'react';
import { Typography, CircularProgress, Box, Button, Card, CardContent, Grid } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

interface ProductInfo {
  overview: string;
  features: string;
  benefits: string;
  pricing: string;
}

const cardColors = {
  overview: '#E6F3FF',  // Light Blue
  features: '#FFE6E6',  // Light Red
  benefits: '#E6FFE6',  // Light Green
  pricing: '#FFE6FF',   // Light Purple
};

const ProductDetails: React.FC = () => {
  const { productName } = useParams<{ productName: string }>();
  const navigate = useNavigate();
  const [productInfo, setProductInfo] = useState<ProductInfo>({
    overview: '',
    features: '',
    benefits: '',
    pricing: ''
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const formatProductName = (name: string): string => {
    return name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  useEffect(() => {
    const fetchProductDetails = async () => {
      if (fetchedRef.current) return;
      fetchedRef.current = true;

      setProductInfo({
        overview: '',
        features: '',
        benefits: '',
        pricing: ''
      });
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`http://localhost:5000/product-details/${encodeURIComponent(productName || '')}`);
        if (!response.ok) {
          throw new Error('Failed to fetch product details');
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'stop') {
                  setLoading(false);
                } else if ('overview' in data) {
                  // This is a cache hit, set all data at once
                  setProductInfo(data);
                  setLoading(false);
                  break;
                } else if (data.type === 'content') {
                  setProductInfo(prev => ({
                    ...prev,
                    [data.section]: (prev[data.section as keyof ProductInfo] || '') + data.content
                  }));
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
    <Box sx={{ maxWidth: 1200, margin: 'auto', mt: 4, px: 2 }}>
      <Button onClick={() => navigate(-1)} sx={{ mb: 2 }}>Back to Products</Button>
      <Typography variant="h4" gutterBottom>{formatProductName(productName || '')}</Typography>
      <Grid container spacing={2}>
        {Object.entries(productInfo).map(([section, content]) => (
          <Grid item xs={12} md={section === 'overview' ? 12 : 6} key={section}>
            <Card sx={{ height: '100%', backgroundColor: cardColors[section as keyof typeof cardColors] }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>{section.charAt(0).toUpperCase() + section.slice(1)}</Typography>
                <ReactMarkdown>{content || 'No information available.'}</ReactMarkdown>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProductDetails;