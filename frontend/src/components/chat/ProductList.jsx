import React from 'react';
import ProductCard from './ProductCard';

function ProductList({ products }) {
  if (!products || products.length === 0) {
    return (
      <div className="p-8 text-center text-gray-400">
        <p>No products to display</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {products.map((product, index) => (
        <ProductCard 
          key={`${product.id || 'product'}-${index}`} 
          product={product} 
        />
      ))}
    </div>
  );
}

export default ProductList;
