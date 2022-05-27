txtfiles=dir('*.txt');
xlsfiles=dir('*.xlsx');
for j=2:length(xlsfiles)
    %% Import station data from spreadsheet
    % Script for importing data from the following spreadsheet:
    
    cur_xls=xlsfiles(j).name;
    % Setup the Import Options and import the data
    opts = spreadsheetImportOptions("NumVariables", 15);
    
    % Specify sheet and range
    opts.Sheet = "Report Data";
    opts.DataRange = "A2:O129";
    
    % Specify column names and types
    opts.VariableNames = ["Fwy", "District", "County", "City", "CAPM", "AbsPM", "Length", "ID", "Name", "Lanes", "Type", "SensorType", "HOV", "MSID", "IRM"];
    opts.VariableTypes = ["string", "double", "string", "categorical", "string", "double", "double", "double", "string", "double", "string", "categorical", "categorical", "string", "string"];
    
    % Specify variable properties
    opts = setvaropts(opts, ["Fwy", "County", "CAPM", "Name", "Type", "MSID", "IRM"], "WhitespaceRule", "preserve");
    opts = setvaropts(opts, ["Fwy", "County", "City", "CAPM", "Name", "Type", "SensorType", "HOV", "MSID", "IRM"], "EmptyFieldRule", "auto");
    
    % Import the data
    tempstr1="D:\Summer_Project\Data\";
    file_name=append(tempstr1,cur_xls)
    Excel_data = readtable(file_name, opts, "UseExcel", false);
    
    
    % Clear temporary variables
    clear opts tempstr1
    
    %% read hourly data from txt
    Dist=table2array(unique(Excel_data(:,2)));
    Dist=Dist(~isnan(Dist));
    Dist=Dist(1);
    tempstr='d0%d';
    distid=sprintf(tempstr,Dist);
    
    for i=1:length(txtfiles)
        cur_name=txtfiles(i).name;
        if contains(cur_name,distid)
            
            opts = delimitedTextImportOptions("NumVariables", 42);
            
            % Specify range and delimiter
            opts.DataLines = [1, Inf];
            opts.Delimiter = ",";
            
            % Specify column names and types
            opts.VariableNames = ["Timestamp", "Station", "Dist", "Route", "Direction", "Type", "Length", "Samples","Observed", "Flow", "occu", "spd", "delay", "VarName14", "VarName15", "VarName16", "VarName17", "VarName18", "VarName19", "VarName20", "VarName21", "VarName22", "VarName23", "VarName24", "VarName25", "VarName26", "VarName27", "VarName28", "VarName29", "VarName30", "VarName31", "VarName32", "VarName33", "VarName34", "VarName35", "VarName36", "VarName37", "VarName38", "VarName39", "VarName40", "VarName41", "VarName42"];
            opts.VariableTypes = ["string", "double", "double", "double", "string", "string", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double", "string", "string", "string", "string", "string", "string"];
            
            % Specify file level properties
            opts.ExtraColumnsRule = "ignore";
            opts.EmptyLineRule = "read";
            
            % Specify variable properties
            opts = setvaropts(opts, ["Timestamp", "Direction", "Type", "VarName37", "VarName38", "VarName39", "VarName40", "VarName41", "VarName42"], "WhitespaceRule", "preserve");
            opts = setvaropts(opts, ["Timestamp", "Direction", "Type", "VarName37", "VarName38", "VarName39", "VarName40", "VarName41", "VarName42"], "EmptyFieldRule", "auto");
            
            % Import the data
            txt_data = readtable(cur_name, opts);
            
            
            %Clear temporary variables
            clear opts
            %%
            Interested_type='HOV';
            Interested_sid=table2array(Excel_data(table2array(Excel_data(:,11))==Interested_type,8)); %HOV station id
            Reduced_table=txt_data(~isnan(table2array(txt_data(:,10))),:); %find all horly data with positive flow input
            Sid_avaliable=table2array(Reduced_table(:,2));                 %get all station id        
            HOV_id=ismember(Sid_avaliable,Interested_sid);                 %overlap of station data and hourly data
            HOV_data=Reduced_table(HOV_id,:);                              %HOV station in the interested site
            HOV_data_reduced=HOV_data(table2array(HOV_data(:,9))>90,:);    %find % observerd >90
            Stations=table2array(unique(HOV_data_reduced(:,2)));           %following lines are average detector health by month
            Observed_data=zeros(length(Stations),2);
            Observed_data(:,1)=Stations;
            for k=1:length(Stations)
                temp=HOV_data_reduced(table2array(HOV_data_reduced(:,2))==Stations(k),:);
                avg1=mean(table2array(temp(:,9)));
                Observed_data(k,2)=avg1;
            end
            str1=string(extractBefore(cur_xls,".xls"));                    %dump output in txt file
            str2=string(extractAfter(cur_name,"_hour"));
            str0='D:\Avg_detector_health_';
            file_dump=append(str0,str1,str2);
            fileID = fopen(file_dump,'w');
            fprintf(fileID,'%d %d\n',Observed_data');
            fclose(fileID);
            clear temp Observed_data
            
            
        end
        
        
        
        
    end
end