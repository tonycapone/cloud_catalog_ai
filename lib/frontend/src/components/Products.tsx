import React, { useState, useEffect, useRef } from 'react';
import { Grid, Card, CardContent, CardActions, Button, Typography, CircularProgress, Box } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';

// Add all Font Awesome solid icons to the library
library.add(fas);

interface Product {
  name: string;
  description: string;
  internal_link: string;
  external_link: string;
  icon: string;
}

const ProductGrid: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const fetchedRef = useRef(false);

  useEffect(() => {
    const fetchProducts = async () => {
      if (fetchedRef.current) return;
      fetchedRef.current = true;
      
      try {
        const response = await fetch('http://localhost:5000/products');
        if (!response.ok) {
          throw new Error('Failed to fetch products');
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
                } else {
                  setProducts(prev => [...prev, data]);
                }
              } catch (error) {
                console.error('Error parsing SSE data:', error);
              }
            }
          }
        }
      } catch (err) {
        console.error('Error fetching products:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
        setLoading(false);
      }
    };

    fetchProducts();
  }, []); // Empty dependency array

  const handleCardClick = (internalLink: string) => {
    console.log('Navigating to:', internalLink);
    navigate(internalLink);
  };

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box>
      {loading && <CircularProgress />}
      <Grid container spacing={2}>
        {products.map((product, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card 
              sx={{ 
                backgroundColor: `rgb(${Math.floor(Math.random() * 56 + 200)}, ${Math.floor(Math.random() * 56 + 200)}, ${Math.floor(Math.random() * 56 + 200)})`,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 6,
                },
              }}
              onClick={() => handleCardClick(product.internal_link)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                  <FontAwesomeIcon icon={['fas', product.icon as any]} size="2x" style={{ marginRight: '16px' }} />
                  <Typography variant="h5" component="div">
                    {product.name}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {product.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button 
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCardClick(product.internal_link);
                  }}
                >
                  Learn More
                </Button>
                {product.external_link && product.external_link !== '#' && (
                  <Button 
                    size="small" 
                    href={product.external_link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    External Link
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProductGrid;