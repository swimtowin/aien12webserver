var express = require('express');

var mysql = require('mysql');
var con = mysql.createConnection({
    host: "aien12four.cxr0m1n24wv8.us-east-1.rds.amazonaws.com",
    user: "aien12four",
    password: "uniqlo12aien",
    database: "images"
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


    module.exports = router;