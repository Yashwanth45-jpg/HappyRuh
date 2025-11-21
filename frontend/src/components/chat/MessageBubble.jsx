import React, { useEffect, useRef } from 'react';

const MessageBubble = ({ message, onShowProducts }) => {
  const isBot = message.type === 'bot';
  const contentRef = useRef(null);
  
  // Add click handlers for show-more buttons after render
  useEffect(() => {
    if (isBot && contentRef.current) {
      const buttons = contentRef.current.querySelectorAll('.show-more-btn');
      
      buttons.forEach(btn => {
        const handleClick = () => {
          const container = btn.parentElement;
          const hiddenTags = container.querySelectorAll('.product-tag.hidden-tag');
          hiddenTags.forEach(tag => {
            tag.classList.remove('hidden-tag');
            tag.style.display = 'inline-block';
          });
          btn.style.display = 'none';
        };
        
        btn.addEventListener('click', handleClick);
        
        // Cleanup
        return () => btn.removeEventListener('click', handleClick);
      });
    }
  }, [isBot, message.text]);
  
  const handleProductsClick = () => {
    if (message.products && message.products.length > 0) {
      onShowProducts(message.products);
    }
  };
  
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg px-4 py-2 ${
          isBot
            ? 'bg-gray-700 text-gray-100'
            : 'bg-blue-600 text-white'
        }`}
      >
        {/* Render HTML for bot messages, plain text for user messages */}
        {isBot ? (
          <div 
            ref={contentRef}
            className="text-sm message-content"
            dangerouslySetInnerHTML={{ __html: message.text }}
          />
        ) : (
          <div className="text-sm">{message.text}</div>
        )}
        
        {/* Show products button if products exist */}
        {isBot && message.products && message.products.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-600">
            <button
              onClick={handleProductsClick}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-600 hover:bg-gray-500 transition-colors w-full"
            >
              <div className="flex items-center gap-2 flex-1">
                <div className="flex -space-x-2">
                  {message.products.slice(0, 3).map((product, index) => (
                    <div
                      key={product.id}
                      className="w-8 h-8 rounded-full overflow-hidden bg-white border-2 border-purple-400"
                      style={{ zIndex: 3 - index }}
                    >
                      <img
                        src={product.image || '/placeholder-product.png'}
                        alt={product.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentElement.innerHTML = `<div class="w-full h-full flex items-center justify-center bg-gray-700"><svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/></svg></div>`;
                        }}
                      />
                    </div>
                  ))}
                </div>
                <span className="text-sm text-purple-300 font-medium">
                  {message.products.length} {message.products.length === 1 ? 'product' : 'products'}
                </span>
              </div>
              <svg 
                className="w-4 h-4 text-gray-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 5l7 7-7 7" 
                />
              </svg>
            </button>
          </div>
        )}
        
        <div className={`text-xs mt-1 opacity-70`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;