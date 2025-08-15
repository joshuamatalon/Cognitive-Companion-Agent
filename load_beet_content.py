"""
Load beet farming content to test cross-domain search capabilities.
This demonstrates that the search system IS domain-agnostic when given appropriate content.
"""

from vec_memory import upsert_many

def load_beet_farming_content():
    """Load actual beet farming information into the database"""
    
    print("Loading beet farming content for cross-domain testing...")
    
    beet_content = [
        # Soil and planting
        "The optimal soil pH for growing beets is between 6.0 and 7.5. Beets prefer slightly acidic to neutral soil conditions for best growth and nutrient uptake.",
        
        "Beets should be planted 2-3 weeks before the last spring frost. They are cool-season vegetables that can tolerate light frosts.",
        
        "Beet seeds should be sown 1/2 to 1 inch deep in the soil. Plant them in rows spaced 12-18 inches apart.",
        
        "Space beet plants 3-4 inches apart after thinning. Proper spacing ensures adequate room for root development.",
        
        # Growing conditions
        "Beets take 50-70 days to mature from seed to harvest. Baby beets can be harvested earlier at 30-40 days.",
        
        "Beets grow best in temperatures between 60-70 degrees Fahrenheit. They are cool-weather crops that struggle in hot conditions.",
        
        "Beets need approximately 1 inch of water per week. Consistent moisture is important for proper root development.",
        
        # Pests and diseases
        "Common pests that attack beet crops include aphids, leaf beetles, and leafminers. Regular monitoring helps early detection.",
        
        "Beet plants are susceptible to leaf spot, root rot, and cercospora leaf spot diseases. Proper spacing and air circulation help prevent disease.",
        
        # Nutrients and care
        "Beets require balanced nutrition with adequate nitrogen, phosphorus, and potassium. A 10-10-10 NPK fertilizer works well.",
        
        "Beets are ready to harvest when they reach 1.5 to 3 inches in diameter. The shoulders of the beet will protrude slightly above soil level.",
        
        "Beets can tolerate frost and light freezes. In fact, cool weather can improve their sweetness.",
        
        # Storage and varieties
        "Store harvested beets in cool, humid conditions at 32-40°F with 90-95% humidity. Remove leaves but leave 1 inch of stem.",
        
        "Companion plants for beets include lettuce, onions, cabbage, and Brussels sprouts. Avoid planting near pole beans.",
        
        "Thin beet seedlings when they are 2-3 inches tall, leaving the strongest plants spaced 3-4 inches apart.",
        
        "Beets may bolt (go to seed prematurely) due to temperature stress or being planted too early in cold soil.",
        
        "Prepare soil for beets by tilling to 8-10 inches deep and adding compost to improve soil structure.",
        
        "Popular beet varieties include Detroit Dark Red, Golden beets, Chioggia (candy cane), and Bull's Blood.",
        
        "Prevent beet root maggots through crop rotation, row covers, and avoiding fresh manure.",
        
        "Beet greens are edible and nutritious. Harvest young leaves for salads or cook mature leaves like spinach."
    ]
    
    # Add metadata
    metadata = {
        "source": "farming_guide",
        "topic": "beet_cultivation",
        "type": "agricultural_information"
    }
    
    try:
        # Load beet content
        ids = upsert_many(beet_content, metadata)
        print(f"Successfully loaded {len(ids)} beet farming chunks")
        
        # Also load the keyword index
        from keyword_search import get_keyword_index
        ki = get_keyword_index()
        for i, content in enumerate(beet_content):
            ki.add_document(f"beet_{i}", content, metadata)
        
        print("Beet content added to both vector and keyword indices")
        return True
        
    except Exception as e:
        print(f"Error loading beet content: {e}")
        return False


if __name__ == "__main__":
    success = load_beet_farming_content()
    if success:
        print("\nBeet farming content loaded successfully!")
        print("The database now contains BOTH AI and farming content.")
        print("The search system should now work cross-domain.")