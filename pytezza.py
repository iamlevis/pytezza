import pyodbc
import os
import sys
import pandas as pd
import pprint
import tempfile

class NetezzaConnector:
    """ Convenience connector to Netezza """
    def __init__(self,nzhost,nzdb,nzuser,nzpass):
        print("WARNING: pytezza hasn't been updated since 2020 since I no longer use it professionally.  Raise any issues in github.")
        self.nzhost = nzhost
        self.nzdb = nzdb
        self.nzuser = nzuser
        self.nzpass = nzpass
        self.connstring = "DRIVER={NetezzaSQL};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s"%(nzhost,nzdb,nzuser,nzpass)

        self.connection = self.getConnection()
        self.dry_run_mode = False
        self.verbosity_level = 0
        
    def __del__(self):
        if self.connection:
            self.disconnect()
        return

    def runDry(self):
        """ """
        self.dry_run_mode=True
    
    def runLive(self):
        """ """
        self.dry_run_mode=False
    
    def setVerbosityLevel(self,vl):
        """ 0 for quiet; 1 for loud """
        if vl in (0,1):
            self.verbosity_level=vl
        else:
            self.verbosity_level=0
    
    def getConnection(self):
        """ """
        try:
            return pyodbc.connect(self.connstring,autocommit=True)
        except Exception as details:
            print("Error connecting using %s"%(self.connstring))
            print(">>> ",details)
            sys.exit()

    def disconnect(self):
        """ """
        if self.connection:
            self.connection.close()
        return
    
    def vprint(self,txt,verbose=True):
        """ """
        if verbose:
            print(txt)
        return
    
    def qdrop(self,table):
        """ """
        self.nzPassthrough("""drop table {table} if exists;""".format(table=table))
    
    def tableExists(self,table):
        """ """
        return self.nzPassthrough("""
            select count(*) as n
            from {db}._V_TABLE
            where tablename=upper('{table}')
        """.format(db=self.nzdb,table=table),withResults=True).N[0]>0
    
    def tableN(self,table):
        """ """
        return self.nzPassthrough("""
            select count(*) as n
            from {table}
        """.format(db=self.nzdb,table=table),withResults=True).N[0]
    
    def nzPassthrough(self,q,withResults=False,printQuery=False,dryRun=False,ignoreErrors=False):
        """ Run a query.  If a resultset is expected, return it as a pandas dataframe.
            if printQuery is true, print the first 50 characters of the query.
            If dryRun is true, print the whole query, but do not run it.
        """
        if (printQuery or self.verbosity_level==1):
            print("nzPassthrough:\n%s\n%s\n%s\n" %(80*"=",q,80*"="))
        if (dryRun or self.dry_run_mode):
            print("nzPassthrough would have run this:\n%s\n\n" %q)
            return None
        
        if self.connection:
            if withResults:
                return pd.read_sql(q, self.connection)
            else:
                try:
                    rs = self.connection.execute(q)
                    self.connection.commit()
                except Exception as details:
                    print("Problem with your query.  Error first, then query below:\n{the_details}\n\n{the_query}".format(the_details=details,the_query=q))
                    if not ignoreErrors:
                        print("Exiting due to query problem.")
                        sys.exit(1)
                    else:
                        print("Ignoring query problem.  You might want to look at that.")
                        pass
                return
        else:
            print("You're not connected, and I'm not going to connect for you.  Fix your application.")
            sys.exit(1)
        return
    qq = nzPassthrough
    
    def nzTableToDf(self,db,tablename):
        """ Given a db and table name, suck that data down to a pandas df. """
        return self.nzPassthrough("select * from %s..%s" %(db,tablename),withResults=True)
        
    def dfToNz(self,df_src,db,tablename,distribute_on="random",clobber=False,nzTypes=(),verbose=False,ignoreLoadErrors=False):
        """ Given a pandas df, push that table to netezza, optionally replace the existing table in Netezza.
            If nzTypes immutable is provided, use those types and to hell with the consequences.
            Otherwise, infer the types.
        """
        fqtable = "%s..%s"%(db,tablename)
        print("Loading %d rows and %d columns into %s."%(df_src.shape[0],df_src.shape[1],fqtable))
        self.vprint("Here is a sample of the source data:\n%s\n"%df_src.head(5),verbose)
        
        if not nzTypes:
            #If were weren't supplied types, guess them ourselves.
            nzTypes=self.getNzTypesFromDf(df_src.dtypes)
        
        if clobber:
            self.vprint("Dropping %s." %fqtable,verbose)
            self.nzPassthrough("drop table %s if exists;"%fqtable)
        
        maxerrors="maxerrors 1"
        if ignoreLoadErrors:
            maxerrors="maxerrors 0"
        
        ddl = ""
        for i in range(len(df_src.columns)):
            #New DDL line for each element.  Trickiness to handle no-comma for last element.
            ddl+="    %s %s%s\n"%(df_src.columns[i],nzTypes[i],(i<len(df_src.columns)-1)*",")
        
        dump=tempfile.mkstemp(".csv")[1]
        self.vprint("Dumping local data to %s." %dump,verbose)
        df_src.to_csv(dump,index=False,header=False,line_terminator="\n")
        self.vprint("Dumped %0.2fMB."%(os.path.getsize(dump)/1024/1024),verbose)
        
        loadcmd="""
            create table {fqtable} as
            select * from external '{dump}'
            (
                {ddl}
            )
            using ( logdir '{tempdir}'
                    delimiter ','
                    {maxerrors}
                    skiprows 0
                    datestyle 'mdy'
                    datedelim '/'
                    encoding 'internal'
                    remotesource 'odbc'
                    quotedvalue double
                  )
            ;
        """.format(fqtable=fqtable,dump=dump,ddl=ddl,tempdir=tempfile.gettempdir(),maxerrors=maxerrors)
        self.vprint("Sending data to Netezza using this statement:\n%s"%loadcmd,verbose)
        self.nzPassthrough(loadcmd)
        lrows = self.nzPassthrough("select count(*) as n from %s" %fqtable,withResults=True).N[0]
        
        print("Done.  We dumped %d rows, and then loaded %d rows." %(len(df_src),lrows))
        return lrows
        
    def nzToDf(self,db,table,where="",order=""):
        """ """
        q = "select * from %s..%s"%(db,table)
        if where:
            q+="\nwhere %s" %where
        if order:
            q+="\norder by %s" %order
        return self.nzPassthrough(q,withResults=True)
        
    def getNzTypesFromDf(self,dftypes):
        """ Try to map.  This is almost vulgar.
            Return a tuple the same size as dftypes."""
        default_nz = "varchar(1024)"
        df2nz = {'int64':'bigint',
                 'int32':'bigint',
                 'float64':'float',
                 'float32':'float',
                 'object':'varchar(1024)'}
        
        nztypes = []
        for t in dftypes:
            nztypes.append(df2nz.get(t.name,default_nz))
        return(tuple(nztypes))
        
    def nzDumpToDisk(self,table,outfile,delimiter=",",order_by=None,compress=False):
        """ """
        if compress:
            print("Compress option is not yet supported.")
        if order_by:
            order_by = "order by "+order_by
        
        print("Dumping %s to %s..." %(table,outfile))
        self.nzPassthrough(r"""
            create external table '{outfile}'
              using (remotesource 'odbc'
                     delim '{delimiter}'
                     escapechar '\'
              ) as
                select *
                from {table}
                {order_by}
        """.format(outfile=outfile,delimiter=delimiter,table=table,order_by=order_by))
        
        return
        
        
def test():
    x = NetezzaConnector("nzhost","dbo","user1","p4ss")

    # Run a query, and if there are results, pull them back as a Pandas DF and print them.
    my_results = x.nzPassthrough("select user,current_timestamp",withResults=True)
    pprint.pprint(my_results)

    # Run a query that doesn't send back a result set.
    x.nzPassthrough("""
        drop table mytest if exists;
        create table mytest as
            select '{value_for_my_field}' as my_field
                   ,current_timestamp as ts
        ;
    """.format(value_for_my_field="somevalue"))

    
if __name__ == "__main__":
    test()


