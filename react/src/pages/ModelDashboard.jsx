import {React,useState,useEffect} from "react";
import {useLocation, Link} from 'react-router-dom';
import axios from 'axios';
import Plot from 'react-plotly.js';
function ModelDashboard() {
    // Grab Information from route
    const location = useLocation()
    const model = location.state
    // Setting up state objects used by component 
    const [model_data, setModel] = useState(null);
    const[features, setFeatures] = useState(null);
    const [currentTab, setCurrentTab] = useState(null);
    const [loading,setLoading] = useState(true);
    // Call to flask server to get the model payload for redering of graph and table
    // Setting of state objects
    useEffect(() => {
         axios.get(`http://35.193.203.116:5000/dashboard/${model}`).then((response) => {
           setModel(response.data);
           setFeatures(Object.entries(response.data.data));
           setCurrentTab(Object.entries(response.data.data)[0][0]);
           setLoading(false);
         });
    },[]);
    // Definition of on click for each tab button
    const handleTabClick = (e) => {
         setCurrentTab(e.target.id);
    };
    // Definition of function to round table values
    function round(num){
        return Math.round(num * 1000) / 1000;
    }
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
        <div className="dashboard_background pt-3 px-5">
        <h1>Model Name: {model_data.model_name}</h1>
        <h5>Model Endpoint: {model_data.public_ip}</h5>
        <h5>Number of Predictions: {model_data.num_preds}</h5>
            <div>
                {/* Definition of tab buttons */}
                { <div className='tabs btn-group'>
                    {features.map((tab, i) =>
                        <button className="btn" key={i} id={tab[0]} disabled={currentTab === `${tab[0]}`} onClick={(handleTabClick)}>{tab[0]}</button>
                    )}
                </div> }
                {/* Definition of tab content */}
                { <div className="content m-3">
                    {features.map((tab, i) =>
                        <div key={i}>
                            {currentTab === `${tab[0]}` && 
                            <div>
                                <div>
                                    <div className="row">
                                        <div id= "graph_col" className="col">
                                        <Plot
                                            data={[
                                                {
                                                    name: "Production",
                                                    x: tab[1].bin_edges,
                                                    y: tab[1].prod.chart_bin_heights,
                                                    type: 'bar',
                                                    marker: {
                                                        color: 'rgb(232,150,17)'
                                                    }
                                                },
                                                {
                                                    name: "Training",
                                                    x: tab[1].bin_edges,
                                                    y: tab[1].train.chart_bin_heights,
                                                    type: 'bar',
                                                    marker: {
                                                        color: 'rgb(28,78,170)'
                                                    }
                                                }
                                                ]}
                                                layout={{autosize: true}}
                                            />
                                        </div>
                                        <div id= "spacer_col" className="col-md-1"/>
                                        <div id="table_col" className="col">
                                            <table id="data_table" className="table mt-3">
                                                <thead className="thead table-dark">
                                                    <tr>
                                                    <th scope="col">{tab[0]}</th>
                                                    <th scope="col">Training</th>
                                                    <th scope="col">Production</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="data-table">
                                                    <tr>
                                                    <th scope="row">Average</th>
                                                    <td>{round(tab[1].train.average)}</td>
                                                    <td>{round(tab[1].prod.average)}</td>
                                                    </tr>
                                                    <tr>
                                                    <th scope="row">Median</th>
                                                    <td>{round(tab[1].train.median)}</td>
                                                    <td>{round(tab[1].prod.median)}</td>
                                                    </tr>
                                                    <tr>
                                                    <th scope="row">Std</th>
                                                    <td>{round(tab[1].train.stddev)}</td>
                                                    <td>{round(tab[1].prod.stddev)}</td>
                                                    </tr>
                                                    <tr>
                                                    <th scope="row">Min</th>
                                                    <td>{round(tab[1].train.min)}</td>
                                                    <td>{round(tab[1].prod.min)}</td>
                                                    </tr>
                                                    <tr>
                                                    <th scope="row">Max</th>
                                                    <td>{round(tab[1].train.max)}</td>
                                                    <td>{round(tab[1].prod.max)}</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>}
                        </div>
                    )}
                </div> }
                <Link to="/">
                    <button className="btn" id="btn-back">Back to Models</button>
                </Link>
            </div>
        </div>
    </div>
    );
}
export default ModelDashboard;
