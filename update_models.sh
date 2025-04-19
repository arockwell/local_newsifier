#\!/bin/bash

# List all Python files
find tests -name "*.py" -type f | while read -r file; do
    # Replace ArticleDB with Article
    sed -i '' 's/ArticleDB/Article/g' "$file"
    
    # Replace EntityDB with Entity
    sed -i '' 's/EntityDB/Entity/g' "$file"
    
    # Replace AnalysisResultDB with AnalysisResult
    sed -i '' 's/AnalysisResultDB/AnalysisResult/g' "$file"
    
    # Replace SentimentAnalysisDB with SentimentAnalysis
    sed -i '' 's/SentimentAnalysisDB/SentimentAnalysis/g' "$file"
    
    # Replace OpinionTrendDB with OpinionTrend
    sed -i '' 's/OpinionTrendDB/OpinionTrend/g' "$file"
    
    # Replace SentimentShiftDB with SentimentShift
    sed -i '' 's/SentimentShiftDB/SentimentShift/g' "$file"
    
    # Replace BaseDB with TableBase
    sed -i '' 's/BaseDB/TableBase/g' "$file"
    
    echo "Updated $file"
done

echo "Done updating model names in test files."
