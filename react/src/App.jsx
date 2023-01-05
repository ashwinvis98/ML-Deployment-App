import Models from './pages/Models';
import ModelDashboard from './pages/ModelDashboard';
import { Route,BrowserRouter,Routes } from 'react-router-dom';
function App() {
  return (
      <BrowserRouter>
        {/* Definition of Routes used by App*/}
        <Routes>
          <Route path="/" element = {<Models/>} />
          <Route path="/:name" element = {<ModelDashboard/>}/>
        </Routes>
      </BrowserRouter>
  );
}

export default App;