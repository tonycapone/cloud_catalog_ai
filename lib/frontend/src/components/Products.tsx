import React, { useState, useEffect, useRef } from 'react';
import { Grid, Card, CardContent, CardActions, Button, Typography, CircularProgress, Box, TextField, Skeleton } from '@mui/material';
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

interface ProductGridProps {
  backendUrl: string;
}

const ProductGrid: React.FC<ProductGridProps> = ({ backendUrl }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [productCount, setProductCount] = useState<number>(12);
  const navigate = useNavigate();
  const fetchedRef = useRef(false);

  useEffect(() => {
    const fetchProducts = async () => {
      if (fetchedRef.current) return;
      fetchedRef.current = true;
      
      try {
        const response = await fetch(`${backendUrl}/products?limit=${productCount}`);
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
  }, [productCount, backendUrl]);

  const handleProductCountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const count = parseInt(event.target.value, 10);
    if (!isNaN(count) && count > 0) {
      setProductCount(count);
      fetchedRef.current = false;
      setProducts([]);
      setLoading(true);
    }
  };

  const handleCardClick = (internalLink: string) => {
    console.log('Navigating to:', internalLink);
    navigate(decodeURIComponent(internalLink));
  };

  const PlaceholderCard = () => (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Skeleton variant="circular" width={40} height={40} sx={{ marginBottom: 2 }} />
        <Skeleton variant="text" sx={{ fontSize: '1.5rem', marginBottom: 1 }} />
        <Skeleton variant="text" sx={{ fontSize: '1rem' }} />
        <Skeleton variant="text" sx={{ fontSize: '1rem' }} />
      </CardContent>
      <CardActions>
        <Skeleton variant="rectangular" width={100} height={36} />
      </CardActions>
    </Card>
  );

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box>
      <TextField
        type="number"
        label="Number of Products"
        value={productCount}
        onChange={handleProductCountChange}
        inputProps={{ min: 1 }}
        sx={{ marginBottom: 2 }}
      />
      <Grid container spacing={2}>
        {loading
          ? Array.from(new Array(productCount)).map((_, index) => (
              <Grid item xs={12} sm={6} md={4} key={`placeholder-${index}`}>
                <PlaceholderCard />
              </Grid>
            ))
          : products.map((product, index) => (
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