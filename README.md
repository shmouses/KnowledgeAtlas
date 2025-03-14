# Knowledge Atlas

A powerful tool for organizing research papers and visualizing knowledge connections. Built with Streamlit, NetworkX, and Pyvis.

## Features

- Create and manage topics for organizing papers
- Add papers and link them to relevant topics
- Track reading progress for each paper
- Interactive graph visualization of knowledge connections
- Persistent storage of your knowledge graph
- Statistics dashboard

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd knowledge-atlas
```

2. Create a virtual environment and activate it:
```bash
python -m venv env
# On Windows:
env\Scripts\activate
# On Unix or MacOS:
source env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Begin by adding topics using the sidebar
4. Add papers and associate them with topics
5. View the interactive knowledge graph visualization
6. Track your reading progress and view statistics

## Project Structure

- `app.py`: Main Streamlit application
- `data_model.py`: Graph data model and operations
- `visualization.py`: Graph visualization using Pyvis
- `persistence.py`: Data persistence functionality
- `requirements.txt`: Project dependencies
- `data/`: Directory for storing graph data (created automatically)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 