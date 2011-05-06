What is Silver?
================
Silver (formerly PyCamps) is inspired by the Perl based `DevCamps project <http://devcamps.org/>`_ created by `EndPoint <http://www.endpoint.com/>`_. The idea is simply to make it easy for developers to have their own little environments to build web applications. 

Silver Overview
----------------
Silver is built to enable work on several projects in small, reusable areas, called camps.  Focused on web applications, Silver helps to make quick and easy-to-manage environments.  Each camp uses version control, and gives the developer ultimate control.  Silver enables an easy workflow for quality assurance, integration testing and deployment to production for each project in similar workflows.

The relationship between projects and camps is important.  Each camp must refer to an existing, active project when initialized.  When a camp is run through the qa process, or pushed live, the code in the camp is reintegrated back into the project's master repository.  This process allows new camps to keep the latest code from the live servers available.  In addition, each project can and likely will, have a database which can be cloned.  This allows easy access to data as close to live without actually giving the developer access to the live servers.  A developer can also dig in on a problem quickly and easily, rather than waiting for an admin to give them access to a shared database or virtual machine.

Finally, Silver is not the end all, be all of code development, integration and management.  It's intended to be a development/integration environment for many projects, but at some point it may not scale.  Silver can live on one box and the database another, but at some point another box would have to be created or expanded.  If the database becomes very large, syncronization could be an issue.  Many of these items could be dealt with from the administrators end as well.  I would love feedback on how you use Silver and how you scaled it to solve these or other issues. 

Why use Silver?
----------------
What Silver provides compared with other technologies is the ability to manage a single system, with everything intact.  This allows multiple development projects to live in harmony on a single server.  Using a virtual machine for each developer can be costly (owning hardware, maintenance and downtime).  With Silver, a single physical or virtual machine can run several camps all at the same time.  In addition, Silver provides flexible adaptations to manage several projects from within one system.  In this way, the control resides with the administrators and developers at the same time.

Adding caching servers, code optimization services and other administrative things is completely possible as well. In most applications, these features are configured and ready for use. Tools like memcached, eaccelerator, etc. can be installed by the administrator and used in each and every camp. While it may require a bit of finagling to get it just right, adding extra services to enable performance and convenience is completely possible. 

It is possible that some camps may conflict with certain technologies.  In reality, Silver development environments usually focus on the same programming language. Thus not usually running into this issue. If such a thing does occur, performance is usually good enough on camps to suffice a developer without the conflicting add-on.
