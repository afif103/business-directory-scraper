import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.scraper import scrape_business_directory

# Custom CSS for colors
st.markdown("""
<style>
    .main-header {
        color: #FF6B6B;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
    }
    .sub-header {
        color: #4ECDC4;
        font-size: 1.5em;
        text-align: center;
    }
    .success-msg {
        background-color: #D4EDDA;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
    }
    .stButton>button {
        background-color: #FF6B6B;
        color: white;
        border-radius: 10px;
        font-size: 1.2em;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #4ECDC4;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏢 Business Directory Scraper 🏢</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Extract business info from directories with AI magic! ✨</div>', unsafe_allow_html=True)

st.markdown("🔗 Enter the URL of a business directory to scrape and extract business information.")

url = st.text_input("Directory URL", placeholder="https://example.com/directory")

if st.button("🚀 Scrape Directory"):
    if url:
        with st.spinner("🔍 Scraping and extracting data... Please wait!"):
            try:
                data = scrape_business_directory(url)
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    st.success("✅ Scraping completed! Found {} businesses.".format(len(data)))
                    st.balloons()
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name='businesses.csv',
                        mime='text/csv',
                        key='download-csv'
                    )
                elif isinstance(data, str) and data.strip():
                    st.success("✅ Scraping completed! Raw data extracted.")
                    st.text_area("Extracted Business Information", data, height=300)
                    # For CSV, perhaps add a note
                    st.info("💡 Raw text extracted. CSV export not available for raw data.")
                else:
                    st.warning("⚠️ No businesses found. Try a different URL.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
    else:
        st.warning("⚠️ Please enter a valid URL.")

st.markdown("---")
st.markdown("🛠️ Built with ❤️ using LangChain, Chroma, and Streamlit.")