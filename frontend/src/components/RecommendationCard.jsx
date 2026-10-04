import React from 'react';

const RecommendationCard = ({ title, subtitle, content, reason, icon, color, buttonText, onButtonClick }) => {
  return (
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-secondary hover:shadow-md transition-all duration-300 group">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-2xl ${color} text-white`}>
          {icon}
        </div>
        <span className="text-xs font-medium text-secondary-dark bg-secondary-light px-3 py-1 rounded-full">
          {subtitle}
        </span>
      </div>
      
      <h3 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-primary transition-colors">
        {title}
      </h3>
      
      <p className="text-slate-600 text-sm mb-4 line-clamp-2">
        {content}
      </p>
      
      <div className="bg-secondary-light p-3 rounded-xl mb-6">
        <p className="text-xs text-slate-500 italic">
          <span className="font-bold not-italic">Why? </span> {reason}
        </p>
      </div>
      
      <button 
        onClick={onButtonClick}
        className="w-full py-3 bg-primary text-white rounded-xl font-semibold hover:bg-primary-dark transition-all active:scale-95"
      >
        {buttonText}
      </button>
    </div>
  );
};

export default RecommendationCard;
