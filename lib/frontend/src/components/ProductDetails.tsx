import React, { useState, useEffect, useRef } from 'react';
import { Typography, CircularProgress, Box, Button, Card, CardContent, Grid, Paper } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faListUl, faStar, faDollarSign } from '@fortawesome/free-solid-svg-icons';

interface ProductDetailsProps {
  backendUrl: string;
}

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

const ProductDetails: React.FC<ProductDetailsProps> = ({ backendUrl }) => {
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

  const sectionIcons = {
    overview: faInfoCircle,
    features: faListUl,
    benefits: faStar,
    pricing: faDollarSign,
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
        const response = await fetch(`${backendUrl}/product-details/${encodeURIComponent(productName || '')}`);
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
  }, [productName, backendUrl]);

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box sx={{ maxWidth: 1200, margin: 'auto', mt: 4, px: 2 }}>
      <Button onClick={() => navigate(-1)} sx={{ mb: 2 }}>
        <FontAwesomeIcon icon="arrow-left" style={{ marginRight: '8px' }} />
        Back to Products
      </Button>
      <Paper elevation={3} sx={{ p: 3, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <FontAwesomeIcon icon="cube" style={{ marginRight: '16px' }} />
          {formatProductName(productName || '')}
        </Typography>
      </Paper>
      <Grid container spacing={3}>
        {Object.entries(productInfo).map(([section, content]) => (
          <Grid item xs={12} md={section === 'overview' ? 12 : 6} key={section}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', color: '#1976d2' }}>
                  <FontAwesomeIcon icon={sectionIcons[section as keyof typeof sectionIcons]} style={{ marginRight: '12px' }} />
                  {section.charAt(0).toUpperCase() + section.slice(1)}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <ReactMarkdown>{content || 'No information available.'}</ReactMarkdown>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProductDetails;