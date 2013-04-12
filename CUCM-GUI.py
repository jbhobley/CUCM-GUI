#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      J0277261
#
# Created:     06/11/2012
# Copyright:   (c) J0277261 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import gtk, gobject
import callmanager
import sqlite3

class CUCM_GUI:
    def __init__(self):
        filename="CUCM.glade"
        self.builder=gtk.Builder() # Create a Builder object
        self.builder.add_from_file(filename) # Add all the components from the file
        self.builder.add_objects_from_file(filename, ('btnQuery'))  # Add the objects from the file
        self.window=self.builder.get_object('window1')    # Get the window1 object...
        self.window.show_all()   # and show it
        self.btnUpdate=self.builder.get_object('btnQuery')
        self.entryName=self.builder.get_object('entryName')
        self.entryNumber=self.builder.get_object('entryNumber')
        self.entryModel=self.builder.get_object('entryModel')
        self.status=self.builder.get_object('recordcount')
        # self.textSQL=self.builder.get_object('textSQL')
        self.listStore=self.builder.get_object('liststore1')
        self.treeView=self.builder.get_object('treeview1')
            # connect radiobutton1
        radiobutton=self.builder.get_object('radiobutton1')
        radiobutton.connect("toggled",self.callback,"radio-device")
        radiobutton.set_active(True)
            #connect radiobutton2
        radiobutton=self.builder.get_object('radiobutton2')
        radiobutton.connect("toggled",self.callback,"radio-user")
            # connect radiobutton3
        radiobutton=self.builder.get_object('radiobutton3')
        radiobutton.connect("toggled",self.callback,"radio-vm")
            # connect radiobutton4
        radiobutton=self.builder.get_object('radiobutton4')
        radiobutton.connect("toggled",self.callback,"radio-spares")
            # Hide SQL display
        # self.builder.get_object('scrolledwindow1').set_visible(False)
        handlers = {
            "onDeleteWindow":     self.closeWindow,  # gtk.main_quit,
            "onExecutePressed": self.update,
            "on_btnRefresh_clicked": self.refreshData
        }
        self.builder.connect_signals(handlers)

        # self.cm_connection=cm_connection

        self.baseQuery=''
        self.alreadyRun=None

            #initialise cm data

        self.combineData()


    def setBaseQuery(self,query):
        self.baseQuery=query

    def refreshData(self,q1=None):
        self.combineData()


    def update(self,button):
        cursor=gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.window.get_root_window().set_cursor(cursor)
        self.setStatus('Searching, please wait')

        name =self.entryName.get_text().lower()
        number=self.entryNumber.get_text().lower()
        model=self.entryModel.get_text().lower()
        namequery=""
        numberquery=""
        modelquery=""
        first=True
        if (len(name)>0):
            if first: namequery=' WHERE '; first=False
            else: namequery=' AND '
            namequery=namequery+( '(LOWER(description) like "%'+name+'%" OR \
                        LOWER(alertingname) like "%'+name+'%" OR \
                        LOWER(user.lastname) like "%'+name+'%" OR\
                        LOWER(user.firstname) like "%'+name+'%" OR\
                        LOWER(unity.lastname) like "%'+name+'%" OR\
                        LOWER(unity.firstname) like "%'+name+'%")')
        if (len(number)>0):
            if first: numberquery=' WHERE '; first=False
            else: numberquery=' AND '
            numberquery=numberquery+('(dn like "%'+number+'%" OR \
                                DTMFAccessId like "%'+number+'%")')
        if(len(model)>0):
            if first: modelquery=' WHERE '; first=False
            else: modelquery=' AND '
            modelquery=modelquery+('LOWER(devicetype) like "%'+model+'%"')
        extraquery= namequery+numberquery + modelquery
        query=self.baseQuery+extraquery

        resultList=self.getCombinedData(query)


        if (len(resultList)<2):
            self.listStore.clear()                  # clear the results listStore down
            self.setStatus('Sorry, no records found')
        else:
            self.setStatus(str(len(resultList)-1)+' Records found')
            tvcolumns=[]

            if not (self.alreadyRun):
                for col in self.treeView.get_columns():
                    self.treeView.remove_column(col)
                colnum=0
                # Step through the columns in the header row of the list
                for head in resultList[0]:
                    thiscol=gtk.TreeViewColumn(head)    # create a treeview column with the column title
                    thiscol.set_sort_column_id(colnum)  # Set the column sortable
                    thiscol.set_reorderable(True)
                    thiscol.set_resizable(True)
                    tvcolumns.append(thiscol)           # append the new column to the tvcolumns list
                    self.treeView.append_column(thiscol)# append the new column to the treeView object
                    colnum=colnum+1                 # increment the columnumber
                self.alreadyRun=True

            self.listStore.clear()                  # clear the results listStore down
            for line in resultList[1:]:  # Step through the rows of data
                extendedLine = (line+('','','','','','','','','',''))[0:25]
                self.listStore.append(map(str,extendedLine)) # append the row of data to the listStore

            #self.treeView.set_reorderable(True)     # set the columns in the listView to be reorderable
            #self.treeView.set_search_column(1)   # set the search column
            self.treeView.columns_autosize()

            count=0
            for col in tvcolumns:                   # step through the tvcolumns list

                thiscell=gtk.CellRendererText()     # create a new CellRenderer object to populate this column
                col.pack_start(thiscell, True)      # pack_start (place the cell object at the start of the column)
                col.add_attribute(thiscell, 'text', count) # populate the cell with the contents of column 'count' and format them as text
                if(col.props.title in ['firstname','lastname','userid']):
                    thiscell.set_property("background", 'alice blue')
                    thiscell.set_property("background-set",True)
                elif(col.props.title in ['DisplayName','FirstName','LastName','DtmfAccessId']):
                    thiscell.set_property("background", 'light steel blue')
                    thiscell.set_property("background-set",True)
                else:
                    thiscell.set_property("background", 'white')
                    thiscell.set_property("background-set",True)


                count=count+1                       # next column

        self.window.get_root_window().set_cursor(None)


    def getPassword(self):
        password=self.passwordDialog()
        return password.encode('base64')

    def responseToDialog(self, entry,dialog,response):
        dialog.response(response)

    def passwordDialog(self):
        dialog=gtk.MessageDialog(
            self.window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_markup('Please enter the callmanager password')
        # create the textentry field
        entryPassword=gtk.Entry()
        entryPassword.set_visibility(False)
        # connect 'Enter' to ok button
        entryPassword.connect("activate",self.responseToDialog, dialog, gtk.RESPONSE_OK)
        # creat a horizontal box to pack the dialog and a label
        hbox=gtk.HBox()
        hbox.pack_start(gtk.Label("Password:"), False,5, 5)
        hbox.pack_end(entryPassword)
        dialog.vbox.pack_end(hbox,True,True,0)
        dialog.show_all()

        dialog.run()
        text=entryPassword.get_text()
        dialog.destroy()
        return text

    def waitDialog(self, text):
        dialog=gtk.MessageDialog(
            self.window,
            buttons=gtk.BUTTONS_NONE,
            message_format=text)
        # dialog.set_markup(text)
        image=gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_DIALOG)
        image.show()
        dialog.set_image(image)
        dialog.set_response_sensitive(gtk.RESPONSE_CANCEL,False)
        dialog.set_sensitive(False)
        dialog.show_all()
        #dialog.run()
        return dialog


    def combineData(self):

            # Create a connection to a sqlite3 database in memory

        conn=sqlite3.connect(':memory:')
        self.conn=conn

            # Populate the cm table from the results of a query from callmanager

        query = 'SELECT d.name, d.description, tp.name as devicetype, \
                n.dnorpattern AS dn, part.name as partname, css.name AS cssname,\
                pug.name AS pickupgroup, n.alertingname, \
                vm.name as vmprofile, n.cfaptvoicemailenabled as cfa, n.cfbintvoicemailenabled as cfb, \
                n.cfnavoicemailenabled as cfna \
                FROM device AS d \
                INNER JOIN devicenumplanmap AS dmap ON dmap.fkdevice=d.pkid \
                INNER JOIN numplan AS n ON dmap.fknumplan=n.pkid \
                LEFT JOIN voicemessagingprofile AS vm ON n.fkvoicemessagingprofile=vm.pkid \
                LEFT JOIN routepartition AS part ON n.fkroutepartition=part.pkid \
                LEFT JOIN callingsearchspace AS css ON n.fkcallingsearchspace_sharedlineappear=css.pkid \
                LEFT JOIN typeproduct AS tp ON d.tkproduct=tp.enum \
                LEFT JOIN pickupgrouplinemap AS pu ON n.pkid=pu.fknumplan_line \
                LEFT JOIN pickupgroup AS pug ON pu.fkpickupgroup=pug.pkid \
                WHERE d.tkclass=1'
        server='https://cm-lor-adm2:8443/axl/'
        # password="S1emens!"

            # connect to callmanager and extract data based on query
        try:
            cm=callmanager.callmanager(server,query)
            password=self.getPassword()
            cm.setCredentials(password.decode('base64'))

                # Display a wait dialog
            waitDialog = self.waitDialog('Please wait while the local cache is populated')

            self.setStatus('Initialising data')

            self.setStatus('Get data')

            cm.getCMData()

            self.setStatus('Parse data')

            cm.parseET()
            CMList=cm.getList()

            self.setStatus('Populating local cache')

            tableCols=""
            insertCols=""

                # Iterate through the titles in the first row of the list and set them as the field names
                # while doing this build a string to set the field types when inserting the subsequent rows

            for col in CMList[0]:
                tableCols=tableCols+str(col)+" TEXT, "
                insertCols=insertCols+"?, "
            tablebuild="CREATE TABLE cm("+tableCols[:-2]+")"
            insertbuild="INSERT INTO cm VALUES("+insertCols[:-2]+")"
            print tablebuild
            print insertbuild

                # create a cursor to the sqlite db and create the table and populate with data

            cur=conn.cursor()
            self.cur=cur
            cur.execute("DROP TABLE IF EXISTS cm")
            cur.execute(tablebuild)
            cur.executemany(insertbuild,CMList[1:])


                # now get the user information

            self.setStatus('Getting User data')

            cm.setCMQuery('select firstname,lastname,telephonenumber,userid from enduser')
            cm.getCMData()

            self.setStatus('Parsing User data')

            cm.parseET()
            CMList=cm.getList()

            self.setStatus('Populating local cache')

            tableCols=""
            insertCols=""

                # Iterate through the titles in the first row of the list and set them as the field names
                # while doing this build a string to set the field types when inserting the subsequent rows

            for col in CMList[0]:
                tableCols=tableCols+str(col)+" TEXT, "
                insertCols=insertCols+"?, "
            tablebuild="CREATE TABLE user("+tableCols[:-2]+")"
            insertbuild="INSERT INTO user VALUES("+insertCols[:-2]+")"
            print tablebuild
            print insertbuild

            cur.execute("DROP TABLE IF EXISTS user")
            cur.execute(tablebuild)
            cur.executemany(insertbuild,CMList[1:])





                # connect to unity and extract user data

            userver='https://vm-lor-adm1:8443/vmrest/users'
            unity=callmanager.callmanager(userver,'*')
            unity.setCredentials(password.decode('base64'),'cucadministrator')

            self.setStatus('Getting Unity data')

            unity.getUnityData()

            self.setStatus('Parsing Unity data')

            unity.parseET('User',['DisplayName','DtmfAccessId','FirstName','LastName'])
            unityList=unity.getList()

            unitytableCols=""
            unityinsertCols=""

                # Iterate through the titles in the first row of the list and set them as the field names
                # while doing this build a string to set the field types when inserting the subsequent rows

            self.setStatus('Populating Unity cache')

            for col in unityList[0]:
                unitytableCols=unitytableCols+str(col)+" TEXT, "
                unityinsertCols=unityinsertCols+"?, "
            unitytablebuild="CREATE TABLE unity("+unitytableCols[:-2]+")"
            unityinsertbuild="INSERT INTO unity VALUES("+unityinsertCols[:-2]+")"
            print unitytablebuild
            print unityinsertbuild

                # use the cursor to the sqlite db and create the table and populate with data

            cur.execute("DROP TABLE IF EXISTS unity")
            cur.execute(unitytablebuild)
            cur.executemany(unityinsertbuild,unityList[1:])

            self.setStatus('Data caching complete')

                # Create table to hold all numbers in valid range
            rangetablebuild="CREATE TABLE range(number INT)"
            self.cur.execute("DROP TABLE IF EXISTS range")
            self.cur.execute(rangetablebuild)
            for num in range(3300,4200):
                self.cur.execute("INSERT INTO range VALUES ("+str(num)+")")

        except:
            self.setStatus('Unable to get data from callmanager, loading from offline file')
            self.cur=conn.cursor()
            self.loadOfflineDb()
            self.setStatus('Data caching complete')


        # self.fields=tableCols.replace(' ','').replace('TEXT','').split(',')[:-1]+unitytableCols.replace(' ','').replace('TEXT','').split(',')[:-1]
        # self.cur=cur
        self.setBaseQuery('SELECT cm.*, user.firstname,user.lastname,user.userid, \
                            unity.DisplayName,unity.FirstName,unity.LastName \
                            FROM cm \
                            LEFT JOIN unity ON cm.dn=unity.DtmfAccessId \
                            LEFT JOIN user ON cm.dn=user.telephonenumber')




        waitDialog.destroy()
        pass

    def callback(self,widget,data=None):
            # Display the button pressed and whether it was selected or deselected
            # ("OFF","ON") [widget.get_active()] # displays off for a False and on for True result of get_active
        print "%s was toggled %s" % (data, ("OFF", "ON") [widget.get_active()])
        if('device' in data and widget.get_active()):
            self.setBaseQuery('SELECT cm.*, user.firstname,user.lastname,user.userid, \
                                unity.DisplayName,unity.FirstName,unity.LastName \
                                FROM cm \
                                LEFT JOIN unity ON cm.dn=unity.DtmfAccessId \
                                LEFT JOIN user ON cm.dn=user.telephonenumber')
            self.update(widget)

        elif('user' in data and widget.get_active()):
            self.setBaseQuery('SELECT user.firstname,user.lastname,user.userid, user.telephonenumber, \
                                cm.*, unity.DisplayName,unity.FirstName,unity.LastName \
                                FROM user \
                                LEFT JOIN cm on user.telephonenumber=cm.dn \
                                LEFT JOIN unity ON user.telephonenumber=unity.DtmfAccessId')
            self.update(widget)

        elif('spares' in data and widget.get_active()):
            self.setBaseQuery('SELECT range.number, \
                                cm.*, user.firstname,user.lastname,user.userid \
                                FROM range \
                                LEFT JOIN cm on range.number=cm.dn \
                                LEFT JOIN unity on range.number=unity.DtmfAccessId \
                                LEFT JOIN user ON range.number=user.telephonenumber')
            self.update(widget)

        elif('vm' in data and widget.get_active()):
            self.setBaseQuery('SELECT unity.DisplayName,unity.FirstName,unity.LastName,unity.DtmfAccessId, \
                                cm.*, user.firstname,user.lastname,user.userid \
                                FROM unity \
                                LEFT JOIN cm on unity.DtmfAccessId=cm.dn \
                                LEFT JOIN user ON unity.DtmfAccessId=user.telephonenumber')
            self.update(widget)

        self.alreadyRun=False


    def getCombinedData(self, query):

        self.cur.execute(query)
        # cur.execute('SELECT * FROM cm INNER JOIN unity ON cm.dn=unity.DtmfAccessId')
        combinedList=self.cur.fetchall()
        fields=[]
        for field in self.cur.description:
            fields.append(field[0])


        combinedList.insert(0,tuple(fields))

        return combinedList

    def setStatus(self, message):
        self.status.set_text(message)

        while gtk.events_pending():
          gtk.main_iteration()

    def loadOfflineDb(self):
        cmsql=open('cm.sql','r')
        for line in cmsql.readlines():
            for cmd in line.split(';'):
                if not(('BEGIN' in cmd) or ('COMMIT' in cmd)):
                    self.cur.execute(cmd)
        cmsql.close()

    def saveOfflineDb(self):
        cmsql=open('cm.sql','w')
        for line in self.conn.iterdump():
            cmsql.write(line)

        cmsql.close()


    def closeWindow(self,para1,para2):
        print para1,para2
        self.saveOfflineDb()
        gtk.main_quit()

def main():



    app=CUCM_GUI()
    # app.setBaseQuery(query)

    gtk.mainloop()


    pass

if __name__ == '__main__':
    main()
