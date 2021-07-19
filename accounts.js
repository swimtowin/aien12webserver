var express = require('express');

var mysql = require('mysql');
var con = mysql.createConnection({
    host: "127.0.0.1",
    user: "root",
    password: "123456",
    database: "json",
    port:3306
    
});
var router = express.Router();


router.route('/id')

    // 查筆資源
    .post(function (req, res)
    {

        var sql = "SELECT * FROM `images`.`uniqlo` WHERE(`ID` = '"+ req.body.checkmem + "');"
        console.log(sql)

        con.query(sql, function (err, result) {
            if (err) {
                console.log(err)
            }
            else {
                res.json(result)
            }
        })
        
    });

    router.route('/image')

    // 查筆資源
    .post(function (req, res)
    {

        var sql = "SELECT * FROM try5 WHERE `clothset` like '%"+req.body.url+"%'"
        console.log(sql)

        con.query(sql, function (err, result) {
            if (err) {
                console.log(err)
            }
            else {
                res.json(result)
            }
        })
    
    });
    
    module.exports = router;