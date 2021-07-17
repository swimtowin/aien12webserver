var express = require('express')
  , routes = require('./routes')
  , path = require('path'),
	fileUpload = require('express-fileupload'),
	app = express(),
	mysql      = require('mysql'),
	bodyParser=require("body-parser");
	
var connection = mysql.createConnection({
	host     : 'aien12four.cxr0m1n24wv8.us-east-1.rds.amazonaws.com',
	user     : 'aien12four',
	password : 'uniqlo12aien',
	database : 'images',

});
var accounts = require('./accounts');
connection.connect();
 
global.db = connection;
 
// all environments
app.set('port', process.env.PORT || 8080);
app.set('views', __dirname + '/views');
app.set('view engine', 'ejs');
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '/public')));
app.use(fileUpload());

 
// development only
 
app.get('/', routes.index);//call for main index page
app.post('/', routes.index);//call for signup post 
// app.get('/profile/:id',routes.profile);
app.use('/accounts', accounts);
//Middleware
app.listen(8080)