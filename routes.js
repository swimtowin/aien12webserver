exports.index = function(req, res){
   message = '';
  res.render('./index')
};

exports.profile = function(req, res){
   var message = '';
   var id = req.params.id;
   var sql="SELECT * FROM `uniqlo` WHERE `ID`='"+id+"'"; 
   db.query(sql, function(err, result){
     if(result.length <= 0)
     message = "Profile not found!";
     
     res.render('profile.ejs',{data:result, message: message});
  });
};

