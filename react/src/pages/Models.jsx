import {React,useState, useEffect} from "react";
import Card from 'react-bootstrap/Card';
import {Link} from 'react-router-dom';
import '../index.css';
import axios from 'axios'
function Models() {
  // Setting up state objects used by component
  const [mods, setModels] = useState(null);
  const [loading, setLoading] = useState(true);
  // Call to flask server to get list of models to display
  useEffect(() => {
    axios.get('http://35.193.203.116:5000/listModels').then((response)=>{
      setModels(response.data.models);
      setLoading(false);
    });
  }, []);
  // Before server response has come in
  if(loading){
    return (
      <div className="page_background p-3">
          <div className="dashboard_background pt-3 px-5"/>
      </div>
  );
  }
  return (
    <div className="page_background p-3">
        <div className="model_background py-3 px-5">
          <h1 className="mb-3">Models:</h1>
          {/* For each model returned by server call create a card with a link to that models dashboard*/}
            {mods.map((model, index) => (
              <Card className='model-card m-1' key={index}>
                <Card.Body>
                  <h3 className='h3 ms-3'>{model}</h3>
                </Card.Body>
                <Link to={'/'+model} state={model} class ='stretched-link'></Link>
              </Card>
            ))}
      </div>
    </div>
  );
};

export default Models;
