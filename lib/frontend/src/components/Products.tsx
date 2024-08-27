import React, { useState, useEffect, useRef } from 'react';
import { Grid, Card, CardContent, CardActions, Button, Typography, CircularProgress } from '@mui/material';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';

// Add all Font Awesome solid icons to the library
library.add(fas);

interface Product {
  name: string;
  description: string;
  link: string;
  icon: string;
}

const ProductGrid: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    console.log('ProductGrid useEffect running');
    
    const fetchProducts = async () => {
      if (fetchedRef.current) return;
      fetchedRef.current = true;

      try {
        console.log('Fetching products...');
        const response = await fetch('http://localhost:5000/products');
        if (!response.ok) {
          throw new Error('Failed to fetch products');
        }
        const data = await response.json();
        console.log('Setting products:', data.length);
        setProducts(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching products:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
        setLoading(false);
      }
    };

    fetchProducts();

    return () => {
      console.log('ProductGrid useEffect cleanup');
    };
  }, []);

  console.log('ProductGrid rendering, loading:', loading, 'products:', products.length);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Grid container spacing={2}>
      {products.map((product, index) => (
        <Grid item xs={12} sm={6} md={4} key={index}>
          <Card sx={{ backgroundColor: `rgb(${Math.floor(Math.random() * 56 + 200)}, ${Math.floor(Math.random() * 56 + 200)}, ${Math.floor(Math.random() * 56 + 200)})` }}>
            <CardContent>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <FontAwesomeIcon icon={['fas', product.icon as any]} size="2x" style={{ marginRight: '16px' }} />
              <Typography variant="h5" component="div" style={{ flexGrow: 1 }}>
                {product.name}
              </Typography>
            </div>
              <Typography variant="body2" color="text.secondary">
                {product.description}
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                href={product.link} 
                target="_blank" 
                rel="noopener noreferrer"
                disabled={!product.link || product.link === '#'}
              >
                Learn More
              </Button>
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default ProductGrid;