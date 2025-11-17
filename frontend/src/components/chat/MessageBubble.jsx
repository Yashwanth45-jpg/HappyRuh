import React from 'react';
import ProductList from './ProductList';

const MessageBubble = ({ message }) => {
  const isBot = message.type === 'bot';
  
  // Check if the message contains product data
  const isProductMessage = message.products && Array.isArray(message.products);
  
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg px-4 py-2 ${
          isBot
            ? 'bg-gray-700 text-gray-100'
            : 'bg-blue-600 text-white'
        }`}
      >
        {isProductMessage ? (
          <div className="bg-transparent">
            <ProductList products={message.products} />
          </div>
        ) : (
          <>
            <div className="text-sm">{message.text}</div>
            <div className={`text-xs mt-1 opacity-70`}>
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;