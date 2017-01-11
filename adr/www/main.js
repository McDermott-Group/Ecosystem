// "compile" with command: browserify -t [ babelify ] main.js -o bundle.js
// var React = require('react');
// var ReactDOM = require('react-dom');
// var Plotly = require('plotly.js');
var Redux = require('redux');
var ReactRedux = require('react-redux');

var ws; //websocket
/**************
ACTIONS/data to update:
temps
instrument status:
    Compressor
    ruox
    diode
    power supply
    magnet Voltage
    heat Switch
    pump chart
log
regulating
magging up
pump cart pressure

T O D O :
does log field delete your input if it rerenders in the middle of typing?
make different levels for plot times (1hr, 6hrs, 24hrs, etc)
**************/

/********** ACTIONS ***********/
const UPDATE_TEMPS = Symbol('UPDATE_TEMPS');
const updateTemps = (newState={}) => ({
    type: UPDATE_TEMPS,
    newState
});
const UPDATE_INSTRUMENTS = Symbol('UPDATE_INSTRUMENTS');
const updateInstruments = (newState={}) => ({
    type: UPDATE_INSTRUMENTS,
    newState
});
const UPDATE_LOG = Symbol('UPDATE_LOG');
const updateLog = (newState={datetime:'',message:'',alert:false}) => ({
    type: UPDATE_LOG,
    newState
});
const UPDATE_STATE = Symbol('UPDATE_STATE');
const updateState = (newState={isMaggingUp:true,isRegulating:true, compressorOn:false, pressure:NaN}) => ({
    type: UPDATE_STATE,
    newState
});

/********* STATE REDUCER / STORE ************/
const stateReducer = (state={
    temps: {
        timeStamps:[],
        t60K:[],
        t03K:[],
        tGGG:[],
        tFAA:[]
    },
    instruments: {
        'Compressor': {server: false, connected: false},
        'Ruox Temperature Monitor': {server: false, connected: false},
        'Diode Temperature Monitor': {server: false, connected: false},
        'Power Supply': {server: false, connected: false},
        'Magnet Voltage Monitor': {server: false, connected: false},
        'Heat Switch': {server: false, connected: false},
        'Pump Cart Pressure': {server: false, connected: false}
    },
    log:[],
    isMaggingUp:true,
    isRegulating:true,
    compressorOn:false,
    pressure:NaN,
    PSVoltage:NaN,
    PSCurrent:NaN,
    backEMF:NaN
}, action) => {
    switch (action.type) {
        case UPDATE_LOG:
            var newLog = [...state.log, ...action.newState];
            newLog.sort( (a,b) => b.datetime - a.datetime ); // actually want reverse chronological
            return Object.assign( {}, state, {log: newLog})
        case UPDATE_STATE:
            return Object.assign({},state,action.newState);
        case UPDATE_TEMPS:
            return Object.assign( {}, state, {temps: {
                timeStamps:[...state.temps.timeStamps, ...action.newState.timeStamps.map((n)=>new Date(n))],
                t60K:[...state.temps.t60K, ...action.newState.t60K],
                t03K:[...state.temps.t03K, ...action.newState.t03K],
                tGGG:[...state.temps.tGGG, ...action.newState.tGGG],
                tFAA:[...state.temps.tFAA, ...action.newState.tFAA]
            }})
        case UPDATE_INSTRUMENTS:
            return Object.assign( {}, state, {instruments: Object.assign({},state.instruments,action.newState)})
        default:
            return state;
    }
};

const { createStore } = Redux;
const { Provider, connect } = ReactRedux;
const store = createStore(stateReducer);
const { getState, dispatch } = store;
const { createClass, PropTypes } = React;

/***** TEST STORE *********
console.log(getState());
dispatch(updateLog({dt:67,message:'hello'}));
console.log(getState());
dispatch(updateTemps({
    timeStamps: [1,2],
    t60K: [3,4],
    t03K: [5,6],
    tGGG: [7,8],
    tFAA: [9,0]
}));
dispatch(updateTemps({
    timeStamps: [1,2],
    t60K: [3,4],
    t03K: [5,6],
    tGGG: [7,8],
    tFAA: [9,0]
}));
console.log(getState());
**********************/

/********** COMPONENTS ***********/
const Temp = (props) => {
    var arrow = '\u21E7 ';
    if(props.rate < 0) { arrow = '\u21E9 '; }
    var rate = props.rate;
    if(isNaN(rate)) {
        arrow = ' ';
        rate = 'NaN'
    }
    else { rate = Math.abs(parseFloat(rate)).toFixed(3); }
    // no idea why this is needed.  toPrecision was throwing error, but then
    // still working, so ???
    try {
        var temp = parseFloat(props.temp).toPrecision(4);
    } catch(err) {
        //console.log([props.label,props.temp])
        var temp = props.temp;
    }
    return(
        <div style={{border:'3px solid '+props.color}}>
          <div style={{color:'white', backgroundColor:props.color, display: 'inline-block', width:'33.333%'}}>{props.label}</div>
          <div style={{color:props.color, display: 'inline-block', width:'33.333%'}}>{temp}K</div>
          <div style={{color:props.color, display: 'inline-block', width:'33.333%', fontSize:18}}>
            <span style={{verticalAlign:'bottom'}}>[{arrow+rate}K/sec]</span>
          </div>
        </div>
    )
};
const mapStateToTempProps = (storeState,props) => {
    return {
        temps: storeState.temps
    }
}
const AllTemps = ({temps}) => {
    var end = temps.tFAA.length-1;
    var rate = (tempList) => (tempList[tempList.length-1] - tempList[tempList.length-2])
                            / (temps.timeStamps[tempList.length-1] - temps.timeStamps[tempList.length-2])*1000;
    return(
        <div>
            <Temp label="60K" color="#d62728" temp={temps.t60K[end]} rate={rate(temps.t60K)} />
            <Temp label="03K" color="#2ca02c" temp={temps.t03K[end]} rate={rate(temps.t03K)} />
            <Temp label="GGG" color="#ff7f0e" temp={temps.tGGG[end]} rate={rate(temps.tGGG)} />
            <Temp label="FAA" color="#1f77b4" temp={temps.tFAA[end]} rate={rate(temps.tFAA)} />
        </div>
    )
};
const TempDisplay = connect(mapStateToTempProps)(AllTemps);

const Status = (props) => {
    return(
        <div style={{border:'3px solid '+props.color}}>
          <div style={{color:'white', backgroundColor:props.color, display: 'inline-block', width:'50%'}}>{props.label}</div>
          <div style={{color:props.color, display: 'inline-block', width:'50%'}}>{""+parseFloat(props.value).toFixed(3)+" "+props.units}</div>
        </div>
    )
};
const mapStateToStatusProps = (storeState,props) => {
    return {
        pressure:storeState.pressure,
        PSVoltage:storeState.PSVoltage,
        PSCurrent:storeState.PSCurrent,
        backEMF:storeState.backEMF
    }
}
const AllStatuses = ({pressure,PSVoltage,PSCurrent,backEMF}) => {
    return(
        <div>
            <Status label="PS Voltage" color="grey" value={PSVoltage} units={"V"} />
            <Status label="PS Current" color="grey" value={PSCurrent} units={"A"} />
            <Status label="Back EMF" color="grey" value={backEMF} units={"V"} />
            <Status label="Pressure" color="grey" value={pressure} units={"mTorr"} />
        </div>
    )
};
const StatusDisplay = connect(mapStateToStatusProps)(AllStatuses);

const Instrument = (props) => {
    return(
        <li style={{listStyle:"none"}}><span style={{color:props.color}}>{'\u25C9 '}</span>{props.label}</li>
    )
};
const mapStateToInstrumentProps = (storeState,props) => {
    return {
        instruments: storeState.instruments
    }
}
const AllInstruments = ({instruments}) => {
    var instrumentStatuses = Object.keys(instruments).map( function(instrName) {
        var statusColor = "#d62728"; //red
        if( instruments[instrName].server==true && instruments[instrName].connected==false ) {
            statusColor="#ff7f0e"; //orange
        }
        else if( instruments[instrName].server==true && instruments[instrName].connected==true ) {
            statusColor="#2ca02c"; //green
        }
        return <Instrument label={instrName} color={statusColor} />
    });
    return(<ul>{instrumentStatuses}</ul>)
};
const InstrumentDisplay = connect(mapStateToInstrumentProps)(AllInstruments);

const mapStateToOpenHSProps = (storeState,props) => {
    return {
        instruments: storeState.instruments
    }
}
const mapStateToCloseHSProps = (storeState,props) => {
    return {
        instruments: storeState.instruments
    }
}
const mapStateToMagUpProps = (storeState,props) => {
    return {
        isMaggingUp: storeState.isMaggingUp,
        isRegulating: storeState.isRegulating
    }
}
const mapStateToRegulateProps = (storeState,props) => {
    return {
        isMaggingUp: storeState.isMaggingUp,
        isRegulating: storeState.isRegulating
    }
}
const mapStateToCompressorProps = (storeState,props) => {
    return {
        instruments: storeState.instruments,
        compressorOn: storeState.compressorOn
    }
}

const OpenHSButton = connect(mapStateToOpenHSProps)( ({instruments}) => {
    if (instruments['Heat Switch'].server == true) {
        var buttonStyle = {width:'45%'};
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Open Heat Switch'}));
    } else {
        var buttonStyle = {width:'45%', color: 'grey'};
        var buttonClick = (e) => (null);
    }
    return(
        <div className='button' style={buttonStyle} onClick={(e) => buttonClick(e)}> Open Heat Switch </div>
    )
});
const CloseHSButton = connect(mapStateToCloseHSProps)( ({instruments}) => {
    if (instruments['Heat Switch'].server == true) {
        var buttonStyle = {width:'45%'};
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Close Heat Switch'}));
    } else {
        var buttonStyle = {width:'45%', color: 'grey'};
        var buttonClick = (e) => (null);
    }
    return(
        <div className='button' style={buttonStyle} onClick={(e) => buttonClick(e)}> Close Heat Switch </div>
    )
});
const MagUpButton = connect(mapStateToMagUpProps)( ({isMaggingUp,isRegulating}) => {
    if (isMaggingUp) {
        var buttonStyle = {};
        var text = 'Stop Magging Up';
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Stop Magging Up'}));
    }
    else if (isRegulating) {
        var buttonStyle = {color: 'grey'};
        var text = 'Mag Up';
        var buttonClick = (e) => (null);
    }
    else {
        var buttonStyle = {};
        var text = 'Mag Up';
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Mag Up'}));
    }
    return(
        <div className='button' style={buttonStyle} onClick={(e) => buttonClick(e)}> {text} </div>
    )
});
const RegulateButton = connect(mapStateToRegulateProps)( ({isMaggingUp,isRegulating}) => {
    if (isRegulating) {
        var buttonStyle = {width:"70%"};
        var text = 'Stop Regulating';
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Stop Regulating'}));
    }
    else if (isMaggingUp) {
        var buttonStyle = {width:"70%", color: 'grey'};
        var text = 'Regulate';
        var buttonClick = (e) => (null);
    }
    else {
        var buttonStyle = {width:"70%"};
        var text = 'Regulate';
        var buttonClick = (e) => {
            var tempInput = document.getElementById("regTempField");
            ws.send(JSON.stringify({command:'Regulate',temp:tempInput}))
        };
    }
    return(
        <div style={{fontSize:30}}>
            <div className='button' style={buttonStyle} onClick={(e) => buttonClick(e)}> {text} </div>
            <input type="text"
                    id="regTempField"
                    style={{width:"calc(30% - 30px)", height:50,fontSize:30, textAlign:"center"}}
                    placeholder="T"
                    value={0} />
            K
        </div>
    )
});
const CompressorButton = connect(mapStateToCompressorProps)( ({instruments,compressorOn}) => {
    if (instruments['Compressor'].connected) {
        var buttonStyle = {};
        var text = compressorOn ? 'Stop Compressor' : 'Start Compressor'
        var buttonClick = (e) => ws.send(JSON.stringify({command:'Set Compressor State',on:!compressorOn}));
    }
    else {
        var buttonStyle = {color: 'grey'};
        var text = 'Start/Stop Compressor';
        var buttonClick = (e) => (null);
    }
    return(
        <div className='button' style={buttonStyle} onClick={(e) => buttonClick(e)}> {text} </div>
    )
});
const RefreshInstrumentsButton = () => {
    var buttonClick = (e) => ws.send(JSON.stringify({command:'Refresh Instruments'}));
    return(
        <div className='button' onClick={(e) => buttonClick(e)}> Refresh Instruments </div>
    )
};

const mapStateToLogProps = (storeState,props) => {
    return {
        log: storeState.log
    }
}
const LogView = connect(mapStateToLogProps)( ({log}) => {
    var alerts = log.map( function(oneLog) {
        var utc = oneLog.datetime;
        var message = oneLog.message;
        var alert = oneLog.alert;
        var textColor = alert? "#d62728" : "black"; //red or black
        var d = new Date(0);
        d.setUTCSeconds(utc);
        var textWithTime = '[' + (1+d.getMonth()) + '/' + d.getDate() + '/' + d.getFullYear() + ' '
                        + ("0" + d.getHours()).slice(-2) + ':' + ("0" + d.getMinutes()).slice(-2) + ':' + ("0" + d.getSeconds()).slice(-2) + '] ' + message;
        return( <li color={textColor}>{textWithTime}</li> )
    });
    return(
        <div style={{width:'100%', height:100, textAlign:"left", overflowY:"scroll"}}> <ul style={{listStyle:"none"}}>{alerts}</ul> </div>
    )
});
const LogForm = () => {
    const clickLogButton = (e) => {
        var logInput = document.getElementById("logInput");
        ws.send(JSON.stringify({command:'Add To Log', text:logInput.value}));
        logInput.value = '';
    }
    return(
        <div>
            <input type="text"
                    id="logInput"
                    style={{width:"calc(100% - 50px)"}}
                    placeholder="Log a message..." />
            <button style={{width:50}} onClick={(e) => clickLogButton(e)} >Log</button>
        </div>
    )
};


ReactDOM.render(<Provider store={ store }>
                    <div>
                        <OpenHSButton /><CloseHSButton />
                        <MagUpButton />
                        <RegulateButton />
                        <CompressorButton />
                        <RefreshInstrumentsButton />
                    </div>
                </Provider>,
                document.getElementById("buttonHolder"));
ReactDOM.render(<Provider store={ store }><TempDisplay /></Provider>,
    document.getElementById("tempDisplay"));
ReactDOM.render(<Provider store={ store }><StatusDisplay /></Provider>,
    document.getElementById("statusDisplay"));
ReactDOM.render(<Provider store={ store }><InstrumentDisplay /></Provider>,
    document.getElementById("instrumentStatusDisplay"));
ReactDOM.render(<Provider store={ store }>
                    <div>
                        <LogView />
                        <LogForm />
                    </div>
                </Provider>,
                document.getElementById("logHolder"));


var d3 = Plotly.d3;

window.onload = function(){
    ws = new WebSocket("ws://10.0.1.13:9876/ws");
    //ws = new WebSocket("ws://24.177.124.174:9876/ws");
    //var s = new WebSocket("ws://localhost:1025/");
    ws.onopen = function(e) { console.log("socket opened"); }
    ws.onclose = function(e) { console.log("socket closed"); }
    ws.onmessage = function(e) {
        const newState = JSON.parse(e.data);
        if (newState.hasOwnProperty('temps')) {
            dispatch(updateTemps(newState.temps));
            delete newState.temps;
        }
        if (newState.hasOwnProperty('instruments')) {
            dispatch(updateInstruments(newState.instruments));
            delete newState.instruments
        }
        if (newState.hasOwnProperty('log')) {
            dispatch(updateLog(newState.log));
            delete newState.log;
        }
        dispatch(updateState(newState));
    }

    var plotSpace = d3.select('#tempPlot').node();
    const { getState } = store;
    const { temps } = getState();
    const {timeStamps, t60K, t03K, tGGG, tFAA} = temps;
    var data = [
        {
          type: 'scatter',                    // set the chart type
          mode: 'lines',                      // connect points with lines
          name: 'FAA',
          x: timeStamps,                            // set the x-data
          y: tFAA,                        // set the x-data
          line: {                             // set the width of the line.
            width: 1
          }
        },{
          type: 'scatter',                    // set the chart type
          mode: 'lines',                      // connect points with lines
          name: 'GGG',
          x: timeStamps,                            // set the x-data
          y: tGGG,                        // set the x-data
          line: {                             // set the width of the line.
            width: 1
          }
        },{
          type: 'scatter',                    // set the chart type
          mode: 'lines',                      // connect points with lines
          name: '3K',
          x: timeStamps,                            // set the x-data
          y: t03K,                        // set the x-data
          line: {                             // set the width of the line.
            width: 1
          }
        },{
          type: 'scatter',                    // set the chart type
          mode: 'lines',                      // connect points with lines
          name: '60K',
          x: timeStamps,                            // set the x-data
          y: t60K,                        // set the x-data
          line: {                             // set the width of the line.
            width: 1
          }
        }
        ]
    Plotly.plot( plotSpace, data,
  {
      yaxis: {title: "Temperature [K]"},       // set the y axis title
      xaxis: {
        showgrid: false,                  // remove the x-axis grid lines
      },
      margin: {                           // update the left, bottom, right, top margin
        l: 50, b: 50, r: 10, t: 20
      }
  })

  store.subscribe( () => {
      const { getState } = store;
      const { temps } = getState();
      const {timeStamps, t60K, t03K, tGGG, tFAA} = temps;
      //plotSpace.data[0].x.push(d);
      plotSpace.data[0].x = timeStamps;
      plotSpace.data[0].y = tFAA;
      plotSpace.data[1].x = timeStamps;
      plotSpace.data[1].y = tGGG;
      plotSpace.data[2].x = timeStamps;
      plotSpace.data[2].y = t03K;
      plotSpace.data[3].x = timeStamps;
      plotSpace.data[3].y = t60K;
      Plotly.redraw(plotSpace);
  });

  var addRandomTempDataEverySecond = function() {
      dispatch(updateTemps({
          timeStamps:[new Date()],
          t60K: [20+Math.random()],
          t03K: [15+Math.random()],
          tGGG: [10+Math.random()],
          tFAA: [5+Math.random()]
      }));
      setTimeout(addRandomTempDataEverySecond,500);
  }
  //addRandomTempDataEverySecond()
  var addRandomTempData = function() {
      for (let i = 0; i < 200; i++) {
          var datetime = new Date(1475185904065+1000*i)
          dispatch(updateTemps({
              timeStamps:[datetime],
              t60K: [20+Math.random()],
              t03K: [15+Math.random()],
              tGGG: [10+Math.random()],
              tFAA: [5+Math.random()]
          }));
      }
  }
  //addRandomTempData()
}
window.onresize = function() {
    var plotSpace = d3.select('#tempPlot').node();
    Plotly.Plots.resize(plotSpace);
};
